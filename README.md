# Azure Python Bot

Basic Python code to demonstrate the following concepts:

* How to interact with a Microsoft LUIS (Language Understanding Intelligent Service) app using the LUIS Python SDK. The LUIS app tries to understand operations that the user wants to perform over Azure objects: "show", "create", "delete".
* How to extract relevant information out of the LUIS app API, to extract the intent and the entities.
* How to turn the text-based bot into a voice-based bot, setting the VOICE variable to True in the code. pyaudio is leveraged to interact with the computer's audio system. 