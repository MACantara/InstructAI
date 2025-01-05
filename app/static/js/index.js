document.addEventListener('DOMContentLoaded', () => {
    console.log('Index page JavaScript loaded');
    const generateBtn = document.getElementById('generate');
    const promptInput = document.getElementById('prompt');
    const responseArea = document.getElementById('response');

    generateBtn.addEventListener('click', async () => {
        const prompt = promptInput.value.trim();
        if (!prompt) return;

        try {
            const response = await fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ prompt })
            });

            const data = await response.json();
            responseArea.textContent = data.response;
        } catch (error) {
            console.error('Error:', error);
            responseArea.textContent = 'Error generating response';
        }
    });
});