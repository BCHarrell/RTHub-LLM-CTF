// Handles the toasts displayed under the challenge bar
// Color-codes success/failure messages
document.addEventListener('alpine:init', () => {
    Alpine.store('toast', {
        message: '',
        type: 'success', // 'success' or 'error'
        timeout: null,
        show(message, type = 'success') {
            this.message = message;
            this.type = type;
            clearTimeout(this.timeout);
            this.timeout = setTimeout(() => {
                this.message = '';
                this.type = 'success';
            }, 3000);
        }
    });
});

// Chat interface wrapper to allow for:
// - message sending
// - message receiving
// - history clearing
// - usage tracking
// Cleared when changing the challenge set or clearing history
function chatComponent() {
    return {
        userPrompt: '',
        chatLog: [],
        chatIdCounter: 0,
        rpmUsed: 0,
        tpmUsed: 0,
        nextCheckCountdown: 15,
        usagePollInterval: null,
        countdownInterval: null,

        async sendPrompt() {
            const prompt = this.userPrompt.trim();
            if (!prompt) return;

            // Add user message
            this.chatLog.push({
                id: this.chatIdCounter++,
                sender: "You",
                message: prompt,
                html: marked.parse(prompt)
            });

            this.userPrompt = '';
            this.$nextTick(() => {
                const container = document.getElementById("chat-window");
                container.scrollTop = container.scrollHeight;
            });

            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ message: prompt })
                });

                const data = await response.json();

                if (!data.success) {
                    Alpine.store('toast').show(data.response || "Chat failed", 'error');
                    return;
                }

                // Add aRT response
                this.chatLog.push({
                    id: this.chatIdCounter++,
                    sender: "aRT",
                    message: data.response,
                    html: marked.parse(data.response)
                });

                this.$nextTick(() => {
                    const container = document.getElementById("chat-window");
                    container.scrollTop = container.scrollHeight;
                });

                this.fetchUsage();

            } catch (err) {
                console.error("Chat error:", err);
                Alpine.store('toast').show("Unexpected error contacting aRT", 'error');
            }
        },

        async clearHistory() {
            try {
                const response = await fetch('/api/clear-history', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({}) // body is technically optional but ensures proper POST formatting
                });

                const data = await response.json();

                if (!data.success) {
                    Alpine.store('toast').show(data.response || "Failed to clear chat history", 'error');
                    return;
                }

                this.chatLog = [];
                Alpine.store('toast').show("Chat history cleared", 'success');

            } catch (err) {
                console.error("Clear history error:", err);
                Alpine.store('toast').show("Unexpected error clearing chat history", 'error');
            }
        },

        async fetchUsage() {
            try {
                const response = await fetch('/api/usage', {
                    method: 'GET'
                });

                const data = await response.json();

                if (data.success && data.response) {
                    this.rpmUsed = data.response.requests;
                    this.tpmUsed = data.response.tokens;
                } else {
                    console.error("Failed to fetch usage data", 'error');
                }

                if (data.error) {
                    console.error("Usage fetch error:", data.error);
                }

            } catch (err) {
                console.error("Unexpected error fetching usage:", err);
            }
        },

        startUsagePolling() {
            this.fetchUsage(); // fetch immediately on load

            this.usagePollInterval = setInterval(() => {
                this.fetchUsage();
                this.nextCheckCountdown = 15;
            }, 15000);

            this.countdownInterval = setInterval(() => {
                if (this.nextCheckCountdown > 0) {
                    this.nextCheckCountdown--;
                }
            }, 1000);
        }

    };
}

// File handler for uploading and deleting files
function fileHandler() {
    return {
        filename: '',
        fileContent: '',
        files: [],

        async upload() {
            if (!this.filename.trim() || !this.fileContent.trim()) {
                Alpine.store('toast').show("Filename and file content are required.", 'error');
                return;
            }

            const payload = {
                file: {
                    filename: this.filename,
                    file_content: this.fileContent
                }
            };

            try {
                const response = await fetch('/api/upload-file', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(payload)
                });

                const data = await response.json();

                if (!data.success) {
                    Alpine.store('toast').show(data.response || "Upload failed.", 'error');
                    if (data.error) {
                        console.error("Upload error:", data.error);
                    }
                    return
                }

                Alpine.store('toast').show(data.response || "File uploaded successfully.", 'success');

                this.filename = '';
                this.fileContent = '';
                this.files = [...data.currentFiles]; // Use this to handle overwriting an existing file
                                                    // Alpine gets confused with just setting it directly
            } catch (err) {
                console.error("Network or unexpected error:", err);
                Alpine.store('toast').show("An unexpected error occurred.", 'error');
            }
        },

        async deleteFile(filename) {
            try {
                const response = await fetch('/api/delete-file', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ filename })
                });

                const data = await response.json();

                if (!data.success) {
                    Alpine.store('toast').show(data.response || "Failed to delete file.", 'error');
                    if (data.error) {
                        console.error("Delete error:", data.error);
                    }
                    return;
                }
                
                Alpine.store('toast').show(data.response || "File deleted.", 'success');
                this.files = [...data.currentFiles];

            } catch (err) {
                console.error("Network or unexpected error:", err);
                Alpine.store('toast').show("An unexpected error occurred while deleting.", 'error');
            }
        },

        async viewFile(fname) {
            console.log("Calling viewFile. Filename: ", this.filename);
            try {
                const response = await fetch(`/api/view-file?filename=${encodeURIComponent(fname)}`, {
                    method: 'GET'
                });

                if (!response.ok) {
                    Alpine.store('toast').show("Server error", 'error');
                    console.error("Non-200 response from /api/view-file:", response);
                    return;
                }

                const data = await response.json();

                if (!data.success) {
                    Alpine.store('toast').show("File not found", 'error');
                    return;
                }

                // Populate the filename and content fields
                this.filename = data.filename;
                this.fileContent = data.response;

            } catch (err) {
                console.error("Error fetching file content:", err);
                Alpine.store('toast').show("Server error", 'error');
            }
        }
    };
}

// Handles the challenge selector
// When changed:
// - Updates the challenge selection
// - Clears the chat window
// - Updates the objectives view to match the new challenge
function challengeSelector() {
    return {
        selected: '',
        newChallengeSet: '',

        async submitChallengeSet() {
            if (!this.newChallengeSet) return;

            try {
                const response = await fetch('/api/change-challenge-set', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ challenge: this.newChallengeSet })
                });

                const data = await response.json();

                if (!data.success) {
                    Alpine.store('toast').show(data.response || "Failed to update challenge set.", 'error');
                    return;
                }

                this.selected = this.newChallengeSet;
                
                // Add system message to chat log
                const chatComponent = document.querySelector('[x-data^="chatComponent"]')?._x_dataStack?.[0];
                if (chatComponent) {
                    chatComponent.chatLog.push({
                        id: chatComponent.chatIdCounter++,
                        sender: "system",
                        message: "---------- SETTINGS CHANGED: " + this.newChallengeSet.toUpperCase() + " ----------",
                        html: "---------- SETTINGS CHANGED ----------"
                    });
                }
                
                // Scroll the log if needed
                this.$nextTick(() => {
                    const container = document.getElementById("chat-window");
                    container.scrollTop = container.scrollHeight;
                });

                // Update the objectives view to match the new challenge set
                const objectivesComponent = document.querySelector('.objectives-panel')?._x_dataStack?.[0];
                if (objectivesComponent) {
                    objectivesComponent.updateChallengeSet(this.newChallengeSet);
                }

            } catch (err) {
                console.error("Challenge set change error:", err);
                Alpine.store('toast').show("Unexpected error updating challenge set.", 'error');
            }
        }
    };
}

// Handles flag submission
// On success, updates the objectives view
// Flags are only valid for the current challenge set
function flagHandler() {
    return {
        flag: '',

        async submitFlag() {
            const trimmed = this.flag.trim();
            if (!trimmed) return;

            try {
                const response = await fetch('/api/submit-flag', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ flag: trimmed })
                });

                const data = await response.json();

                Alpine.store('toast').show(data.response || "Unexpected response.", data.success ? 'success' : 'error');
                this.flag = '';

                if (data.success) {
                    /// Refresh objectives via the component
                    const tracker = document.querySelector('[x-data^="objectivesTracker"]')?._x_dataStack?.[0];
                    if (tracker) {
                        tracker.refreshObjectives();
                    }
                }

            } catch (err) {
                console.error("Flag submission error:", err);
                Alpine.store('toast').show("Server error. Try again.", 'error');
            }
        }
    };
}

// Handles the objectives view
// - Loads objectives from the server
// - Filters objectives based on the selected challenge set
// - Updates the description panel when an objective is clicked
// - Refreshes the objectives when a flag is submitted
function objectivesTracker() {
    return {
        allObjectives: {},
        challenge: '', // populated from the DOM
        filteredObjectives: [],

        loadObjectives() {
            this.challenge = document.body.dataset.challenge || 'set-1';

            fetch('/api/objective-status')
                .then(response => response.json())
                .then(data => {
                    if (!data.success || !data.response) {
                        Alpine.store('toast').show('Failed to load objectives.', 'error');
                        return;
                    }

                    this.allObjectives = data.response;
                    this.updateFiltered();
                })
                .catch(err => {
                    console.error('Error fetching objectives:', err);
                    Alpine.store('toast').show('Could not fetch objectives.', 'error');
                });
        },

        updateFiltered() {
            this.filteredObjectives = this.allObjectives[this.challenge] || [];
        },

        updateChallengeSet(newDiff) {
            this.challenge = newDiff;
            this.updateFiltered();
        },

        fetchDescription(objectiveId) {
            fetch(`/api/objective-description?id=${encodeURIComponent(objectiveId)}`)
                .then(res => res.json())
                .then(data => {
                    if (data.success && data.response) {
                        const descComponent = document.querySelector('.objective-description-panel')?._x_dataStack?.[0];
                        if (descComponent) {
                            descComponent.set(data.response);
                        }
                    } else {
                        Alpine.store('toast').show("Failed to load description.", 'error');
                    }
                })
                .catch(err => {
                    console.error('Failed to fetch description:', err);
                    Alpine.store('toast').show("Error fetching description.", 'error');
                });
        }
,

        refreshObjectives() {
            fetch('/api/objective-status')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        this.allObjectives = data.response;
                        this.updateFiltered();
                    }
                })
                .catch(err => console.error('Objective refresh error', err));
        }
    };
}

// Handles the objective description panel
// - Displays the title, description, and hint for the selected objective
// - Toggles the hint visibility
// - Updates when a new objective is selected
function objectiveDescription() {
    return {
        title: 'Objective Title',
        description: 'Select an objective on the left to see its description.',
        hint: 'Objective hint',
        showHint: false,

        set(data) {
            this.title = data.title;
            this.description = marked.parse(data.description);
            this.hint = data.hint;
            this.showHint = false;  // Reset hint visibility when new objective is selected
        },

        toggleHint() {
            this.showHint = !this.showHint;
        }
    };
}
