const API_URL = '/api/';
const converter = new showdown.Converter();
let promptToRetry = null;
let uniqueIdToRetry = null;

const submitButton = document.getElementById('submit-button');
const regenerateResponseButton = document.getElementById('regenerate-response-button');
const promptInput = document.getElementById('prompt-input');
const responseList = document.getElementById('response-list');
let isGeneratingResponse = false;

let loadInterval = null;

promptInput.addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
        event.preventDefault();
        if (event.ctrlKey || event.shiftKey) {
            document.execCommand('insertHTML', false, '<br/><br/>');
        } else {
            getGPTResult();
        }
    }
});

function generateUniqueId() {
    const timestamp = Date.now();
    const randomNumber = Math.random();
    const hexadecimalString = randomNumber.toString(16);

    return `id-${timestamp}-${hexadecimalString}`;
}


function addResponse(selfFlag, prompt, timestamp) {
    const uniqueId = generateUniqueId();
    const formattedTimestamp = new Date(timestamp).toLocaleString(); // Ensure timestamp is formatted correctly
    console.log("Adding response with timestamp:", formattedTimestamp); // Debug log
    
    const html = `
        <div class="response-container ${selfFlag ? 'my-question' : 'chatgpt-response'}">
            <img class="avatar-image" src="../../static/chat/img/${selfFlag ? 'me' : 'chatgpt'}.png" alt="avatar"/>
            <div class="prompt-content" id="${uniqueId}">
                <div class="message-content">${prompt}</div>
                <div class="timestamp">${formattedTimestamp}</div>
            </div>
        </div>
    `;
    responseList.insertAdjacentHTML('beforeend', html);
    responseList.scrollTop = responseList.scrollHeight;
    return uniqueId;
}


function loader(element) {
    element.textContent = '';

    loadInterval = setInterval(() => {
        element.textContent += '.';

        if (element.textContent === '....') {
            element.textContent = '';
        }
    }, 300);
}

function setErrorForResponse(element, message) {
    element.innerText = message;
    element.style.color = 'rgb(255, 84, 84)';
}

function setRetryResponse(prompt, uniqueId) {
    promptToRetry = prompt;
    uniqueIdToRetry = uniqueId;
    regenerateResponseButton.style.display = 'flex';
}

async function regenerateGPTResult() {
    try {
        await getGPTResult(promptToRetry, uniqueIdToRetry);
        regenerateResponseButton.classList.add("loading");
    } finally {
        regenerateResponseButton.classList.remove("loading");
    }
}

async function getGPTResult(_promptToRetry, _uniqueIdToRetry) {
    const prompt = _promptToRetry ?? promptInput.textContent;

    if (isGeneratingResponse || !prompt) {
        return;
    }

    submitButton.classList.add("loading");
    promptInput.textContent = '';

    if (!_uniqueIdToRetry) {
        addResponse(true, prompt);
    }

    const uniqueId = _uniqueIdToRetry ?? addResponse(false);
    const responseElement = document.getElementById(uniqueId);
    loader(responseElement);
    isGeneratingResponse = true;

    try {
        const response = await fetch(API_URL + 'get_prompt_result/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ prompt })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        let responseData;
        const contentType = response.headers.get("content-type");
        if (contentType && contentType.indexOf("application/json") !== -1) {
            responseData = await response.json();
        } else {
            responseData = await response.text();
        }

        let responseText;
        if (typeof responseData === 'object') {
            responseText = responseData.reply || JSON.stringify(responseData);
            print("type of response" + typeof responseData === 'object')
        } else if (typeof responseData === 'string') {
            responseText = responseData;
        } else {
            throw new Error('Unexpected response format');
        }

        responseElement.innerHTML = converter.makeHtml(responseText.trim());
        promptToRetry = null;
        uniqueIdToRetry = null;
        regenerateResponseButton.style.display = 'none';

        setTimeout(() => {
            responseList.scrollTop = responseList.scrollHeight;
            hljs.highlightAll();
        }, 10);
    } catch (err) {
        setRetryResponse(prompt, uniqueId);
        setErrorForResponse(responseElement, `Error: ${err.message}`);
    } finally {
        isGeneratingResponse = false;
        submitButton.classList.remove("loading");
    }
}

// async function getMessages() {
//     const currentUrl = window.location.href.split('/');
//     const response = await fetch(API_URL + 'messages/' + currentUrl.at(-2), {
//         method: 'GET',
//         headers: { 'Content-Type': 'application/json' },
//     });

//     if (!response.ok) {
//         console.error('Failed to fetch messages:', response.statusText);
//         return;
//     }

//     const messages = await response.json();
//     console.log("Fetched messages:", messages); // Debug log

//     for (let message of messages) {
//         addResponse(message.is_user, message.message, message.timestamp);
//     }

//     setTimeout(() => {
//         responseList.scrollTop = responseList.scrollHeight;
//         hljs.highlightAll();
//     }, 10);
// }

async function getMessages() {
    const currentUrl = window.location.href.split('/');
    try {
        const response = await fetch(API_URL + 'messages/' + currentUrl.at(-2), {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
        });

        if (!response.ok) {
            const errorText = await response.text();
            console.error('Failed to fetch messages:', response.status, errorText);
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const messages = await response.json();
        console.log("Fetched messages:", messages);

        for (let message of messages) {
            addResponse(message.is_user, message.message, message.timestamp);
        }

        setTimeout(() => {
            responseList.scrollTop = responseList.scrollHeight;
            hljs.highlightAll();
        }, 10);
    } catch (error) {
        console.error('Error in getMessages:', error);
        // Handle the error appropriately (e.g., show an error message to the user)
    }
}

submitButton.addEventListener("click", () => {
    getGPTResult();
});

regenerateResponseButton.addEventListener("click", () => {
    regenerateGPTResult();
});

document.addEventListener("DOMContentLoaded", function(){
    getMessages();
    promptInput.focus();
});
