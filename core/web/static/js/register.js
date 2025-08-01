function registerForm() {
    return {
        username: '',
        reg_code: '',
        errorMessage: '',

        async submit() {
            this.errorMessage = '';

            const formData = new FormData();
            formData.append("username", this.username);
            formData.append("reg_code", this.reg_code);

            try {
                const response = await fetch("/register", {
                    method: "POST",
                    body: formData,
                });

                if (!response.ok) {
                    const data = await response.json();
                    this.errorMessage = data.response || "An unknown error occurred.";
                    return;
                }

                // On success, redirect to the hub interface
                window.location.href = response.url;

            } catch (err) {
                this.errorMessage = "Network error. Please try again.";
            }
        }
    };
}
