document.addEventListener('DOMContentLoaded', () => {
    console.log('Index page JavaScript loaded');
    const generateBtn = document.getElementById('generate');
    const promptInput = document.getElementById('prompt');
    const responseArea = document.getElementById('response');

    generateBtn.addEventListener('click', async () => {
        const prompt = promptInput.value.trim();
        if (!prompt) return;

        try {
            generateBtn.disabled = true;
            generateBtn.textContent = 'Generating...';
            responseArea.textContent = 'Searching and generating response...';

            const response = await fetch('/generate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ prompt })
            });

            const data = await response.json();
            
            // Split response and sources if they exist
            const [mainResponse, ...sourcesParts] = data.response.split('\n\nSources:\n');
            
            // Create main response element
            responseArea.textContent = mainResponse;
            
            // Add sources if they exist
            if (sourcesParts.length > 0) {
                const sourcesSection = document.createElement('div');
                sourcesSection.className = 'sources-section';
                sourcesSection.innerHTML = `<strong>Sources:</strong><br>${sourcesParts.join('')}`;
                responseArea.appendChild(sourcesSection);
            }
        } catch (error) {
            console.error('Error:', error);
            responseArea.textContent = 'Error generating response';
        } finally {
            generateBtn.disabled = false;
            generateBtn.textContent = 'Generate Response';
        }
    });
});