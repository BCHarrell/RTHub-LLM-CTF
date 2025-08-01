# Modifying Basic Guards
A first-stop in defending LLM apps/agents is to add some other guard functionality
that filters input/output. The platform comes with two built-in options:

1. A basic input/output firewall that does some very simple checks using regex
or looking for words within the same sentence. This is pretty easy to beat in
many cases.

2. `llm-guard` implementation using the modules for substrings, regex, prompt 
injection using another language model, and language filters.

## Built-In Guard Considerations
Both the firewall and `llm-guard` implementation are written in English. In fact,
the included `llm-guard` implementation will only allow conversations in English
because using a second language is an easy way to get around English-centric controls 
(which is a lesson to developers! Don't just focus on English for enterprise apps...). 
So if you plan to use a different language to play, you'll want to change those.

For the firewall, just copy the examples for either the regex or same-sentence
checks and fill in the values as desired.

For the `llm-guard`, read [their docs](https://protectai.github.io/llm-guard/) for
various settings and add/remove/tweak modules as desired.

You can also potentially speed up some CPU performance if you're running slow,
again see [their](https://protectai.github.io/llm-guard/tutorials/optimization/) 
docs on ONYX.

## New guards
You can make new guards as desired. Unlike tools and agents, though, these are
**not** auto-loaded. Import them into your desired agent(s) and implement yourself.
If you're modifying the BasicAgent, make sure the `process_message` function
is updated to do the right check(s).
