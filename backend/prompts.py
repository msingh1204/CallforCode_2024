TRANSLATE_TO_ENGLISH = """
Task Description:

You are a language detection and translation assistant. For any given input text, your task is to:

Detect the language of the input text.
Translate the detected language in English.

You MUST return the response in the following JSON format:

{{
"language": "[Detected Language]",
"translation": "[Translated text]"
}}

Return these two properties in this JSON format and NOTHING else.

Example 1:
Input: "Bonjour, je m'appelle Marie."

Output: 
{{ 
    "language": "French",
    "translation": "Hello, my name is Marie."
}}

Example 2:

Input: "¿Dónde está la biblioteca?"

Output: 
{{
"language": "Spanish",
"translation": "Where is the library?"
}}


Example 3:

Input: "Guten Tag, wie geht es Ihnen?"

Output: 
{{
"language": "German",
"translation": "Good day, how are you?"
}}

Example 4:

Input: "私は学生です。"

Output: 

{{
"language": "Japanese",
"translation": "I am a student."
}}

Example 5:

Input: "Привет, как дела?"

Output: 

{{
"language": "Russian",
"translation": "Hi, how are you?"
}}

Now, process the following input according to the task and return ONNLY the JSON output.
Return only the JSON response and do not output any additional characters or information. 
Only return valid JSON output in your reply. 
The response should include only valid JSON.

Input: "{prompt}"
Output:
"""


prompt_to_address = """

Task Description:

You will receive a prompt and your task is two determine the following: 1. The origin address 2. The destination address

Please present your output in the following JSON format::

{{"Origin Address": "Street Address, City, State", "Destination Address": "Street Address, City, State"}}

Return these two properties in this JSON format and NOTHING else.

Example 1:

Prompt: "Help! I am currently stuck in my building at 450 W 20th Street in Manhattan, New York because my floor is flooding.
The storm is very strong and my basement is flooded. I need to get to higher ground. I am trying to get 290 Chamber Street. 
I am trying to get to the Bronx, New York. Please return the safest path for me to get there!":

Output: {{"Origin Address": "450 W 20th Street, Manhattan, New York", "Destination Address": "290 Chamber Street, Bronx, New York"}}

Example 2:

Prompt: "Oh no! There is too much water here! I am currently at 45-63 27th Street in Queens New York. I need to leave soon to get to safety.
I am trying to get to the Bronx New York. I am going to go to 360 E 140th Street. Please provide me with a path to travel there":

Output: {{"Origin Address": "45-63 27th Street, Queens, New York", "Destination Address": "360 E 140th Street, Bronx, New York"}}

Example 3:

Prompt: "There is flooding in my area! Oh no! I need to get to safety from my current location. I am at 302-10 W 160th Street in Bronx New York. I will need to get to higher ground. I need to get to 21-90 W 63rd Street, Manhattan. It's in New York."

Output: {{"Origin Address": "302-10 W 160th Street, Bronx, New York", "Destination Address": "21-90 W 63rd Street, Manhattan, New York"}}

Now you try and return the output ONLY in JSON format and no additional characters:

Prompt: "{text_in}"

Output:
"""

IS_ENGLISH = """Task Description:

You are a language detection assistant. For any given input text, your task is to detect if the language is English.

You MUST return a valid JSON response in the following format with NO additional text

Your JSON string should have a SINGLE property ENGLISH that has a boolean value:

{{"english": "[Output]"}}

Here is an example:

Example 1:

Input: "Bonjour, je m'appelle Marie."

Output: {{"english": false}}

Example 2:

Input: "Hi, how are you doing today?"

Output: {{"english": true}}

Example 3:

Input: "Dónde está la biblioteca?"

Output: {{"english": false}}

Example 4:

Input: "Guten Tag, wie geht es Ihnen?"

Output: {{"english": "false"}}

Now take this input and return a VALID JSON string that has should have a SINGLE property english that has a boolean value:

Input: "{text_in}"
Output:

"""