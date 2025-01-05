document.addEventListener('DOMContentLoaded', () => {
    const generateBtn = document.getElementById('generate');
    const promptInput = document.getElementById('prompt');
    const responseArea = document.getElementById('response');

    const renderSourceLink = (source, title) => {
        // Extract domain from the URL for display
        let displayTitle = title;
        try {
            const url = new URL(source);
            displayTitle = title || url.hostname;
        } catch (e) {
            displayTitle = title || source;
        }
        return `<a href="${source}" target="_blank" class="source-link" rel="noopener noreferrer">
            <i class="fas fa-external-link-alt"></i> ${displayTitle}
        </a>`;
    };

    const renderMetadata = (metadata) => {
        if (!metadata || Object.keys(metadata).length === 0) return '';
        
        let html = '<div class="metadata-section">';
        
        // Render search queries
        if (metadata.search_queries?.length > 0) {
            html += '<div class="search-queries">';
            html += '<h4>🔍 Search Queries:</h4>';
            html += '<ul>';
            metadata.search_queries.forEach(query => {
                html += `<li>${query}</li>`;
            });
            html += '</ul></div>';
        }
        
        // Render all sources in a single container
        if (metadata.chunks?.length > 0) {
            html += '<div class="sources-container">';
            html += '<h4>📚 Sources:</h4>';
            html += '<div class="sources-grid">';
            metadata.chunks.forEach(chunk => {
                html += renderSourceLink(chunk.source, chunk.title);
            });
            html += '</div></div>';
        }
        
        html += '</div>';
        return html;
    };

    generateBtn.addEventListener('click', async () => {
        const prompt = promptInput.value.trim();
        if (!prompt) return;

        try {
            generateBtn.disabled = true;
            generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
            responseArea.innerHTML = '<div class="loading">🔍 Searching and generating response...</div>';

            const response = await fetch('/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt })
            });

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Update response area with main text and metadata
            responseArea.innerHTML = `
                <div class="response-text">${data.response.text}</div>
                ${renderMetadata(data.response.metadata)}
            `;
            
        } catch (error) {
            console.error('Error:', error);
            responseArea.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-circle"></i>
                    Error generating response: ${error.message}
                </div>
            `;
        } finally {
            generateBtn.disabled = false;
            generateBtn.innerHTML = 'Generate Response';
        }
    });
});