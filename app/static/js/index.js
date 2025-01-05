document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('syllabusForm');
    const generateBtn = document.getElementById('generate');
    const topicInput = document.getElementById('topic');
    const responseArea = document.getElementById('response');
    const includeObjectives = document.getElementById('includeObjectives');
    const includeReadings = document.getElementById('includeReadings');

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
        
        // Render sources in grid
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

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const topic = topicInput.value.trim();
        if (!topic) return;

        try {
            generateBtn.disabled = true;
            generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating Syllabus...';
            responseArea.innerHTML = '<div class="loading">🎓 Creating your syllabus...</div>';

            const response = await fetch('/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    topic: topic,
                    include_objectives: includeObjectives.checked,
                    include_readings: includeReadings.checked
                })
            });

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Update response area with syllabus and sources
            responseArea.innerHTML = `
                <div class="syllabus-content">${data.response.text}</div>
                ${renderMetadata(data.response.metadata)}
            `;
            
        } catch (error) {
            console.error('Error:', error);
            responseArea.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-circle"></i>
                    Error generating syllabus: ${error.message}
                </div>
            `;
        } finally {
            generateBtn.disabled = false;
            generateBtn.innerHTML = 'Generate Syllabus';
        }
    });
});