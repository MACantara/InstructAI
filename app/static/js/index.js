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

    const renderSyllabus = (response) => {
        if (response.raw_json) {
            // Use JSON data for more structured rendering
            const json = response.raw_json;
            const content = `
                <div class="syllabus-header">
                    <h1>${json.title}</h1>
                </div>
                
                <div class="course-info">
                    <div class="course-description">
                        <h2>Course Description</h2>
                        ${marked.parse(json.courseDescription)}
                    </div>
                    
                    <div class="course-structure">
                        <h2>Course Structure</h2>
                        <ul>
                            <li><strong>Duration:</strong> ${json.courseStructure.duration}</li>
                            <li><strong>Format:</strong> ${json.courseStructure.format}</li>
                            <li><strong>Assessment:</strong> ${json.courseStructure.assessment}</li>
                        </ul>
                    </div>
                </div>

                <div class="weekly-topics">
                    <h2>Weekly Topics</h2>
                    ${json.weeklyTopics.map(week => `
                        <div class="week-block">
                            <h3>Week ${week.week}: ${week.topic}</h3>
                            <div class="week-content">
                                ${marked.parse(week.description)}
                                ${week.activities ? `
                                    <div class="activities">
                                        <strong>Activities:</strong>
                                        <ul>
                                            ${week.activities.map(activity => `
                                                <li>${activity}</li>
                                            `).join('')}
                                        </ul>
                                    </div>
                                ` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>

                ${json.learningObjectives ? `
                    <div class="objectives">
                        <h2>Learning Objectives</h2>
                        <ul>
                            ${json.learningObjectives.map(obj => `
                                <li>${obj}</li>
                            `).join('')}
                        </ul>
                    </div>
                ` : ''}

                ${json.readings ? `
                    <div class="readings">
                        <h2>Required Readings</h2>
                        <ul>
                            ${json.readings.required.map(reading => `
                                <li>
                                    <strong>${reading.title}</strong> by ${reading.author}
                                    <p>${reading.description}</p>
                                </li>
                            `).join('')}
                        </ul>

                        <h3>Recommended Readings</h3>
                        <ul>
                            ${json.readings.recommended.map(reading => `
                                <li>
                                    <strong>${reading.title}</strong> by ${reading.author}
                                    <p>${reading.description}</p>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                ` : ''}
            `;
            return content;
        } else {
            // Fallback to markdown rendering if no JSON
            return marked.parse(response.text);
        }
    };

    const renderMarkdown = (text) => {
        // Configure marked options
        marked.setOptions({
            breaks: true,        // Convert \n to <br>
            headerIds: true,     // Add IDs to headers for linking
            gfm: true,          // GitHub Flavored Markdown
            smartLists: true,    // Better list handling
            smartypants: true    // Better typography
        });
        
        return marked.parse(text);
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
            
            // Update response area with structured syllabus and sources
            responseArea.innerHTML = `
                <div class="syllabus-content markdown-body">
                    ${renderSyllabus(data.response)}
                </div>
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