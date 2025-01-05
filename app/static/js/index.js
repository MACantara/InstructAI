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

    const renderWeeklyContent = (weekContent) => {
        if (!weekContent) return '';
        
        return `
            <div class="week-content-details">
                <div class="lecture-content">
                    <h4>Lecture Materials</h4>
                    ${marked.parse(weekContent.content.lecture.notes)}
                    
                    <div class="slides-section">
                        <h5>Key Points</h5>
                        <ul>
                            ${weekContent.content.lecture.slides.map(slide => `
                                <li>${slide}</li>
                            `).join('')}
                        </ul>
                    </div>
    
                    ${weekContent.content.lecture.examples.length > 0 ? `
                        <div class="examples-section">
                            <h5>Examples</h5>
                            <pre><code>${weekContent.content.lecture.examples.join('\n\n')}</code></pre>
                        </div>
                    ` : ''}
                </div>
    
                <div class="resources-section">
                    <h4>Additional Resources</h4>
                    
                    ${weekContent.content.resources.videos.length > 0 ? `
                        <div class="videos">
                            <h5>📺 Videos</h5>
                            <ul>
                                ${weekContent.content.resources.videos.map(video => `
                                    <li>
                                        <a href="${video.url}" target="_blank" rel="noopener">
                                            ${video.title}
                                        </a>
                                        - ${video.description}
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
    
                    ${weekContent.content.resources.articles.length > 0 ? `
                        <div class="articles">
                            <h5>📚 Articles</h5>
                            <ul>
                                ${weekContent.content.resources.articles.map(article => `
                                    <li>
                                        <a href="${article.url}" target="_blank" rel="noopener">
                                            ${article.title}
                                        </a>
                                        - ${article.relevance}
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
    
                    ${weekContent.content.resources.tools.length > 0 ? `
                        <div class="tools">
                            <h5>🛠️ Tools</h5>
                            <ul>
                                ${weekContent.content.resources.tools.map(tool => `
                                    <li>
                                        <a href="${tool.url}" target="_blank" rel="noopener">
                                            ${tool.name}
                                        </a>
                                        - ${tool.purpose}
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                    ` : ''}
                </div>
    
                <div class="exercises-section">
                    <h4>Exercises</h4>
                    ${weekContent.content.exercises.map(exercise => `
                        <div class="exercise-item difficulty-${exercise.difficulty}">
                            <h5>${exercise.title}</h5>
                            <p>${exercise.description}</p>
                            <ol>
                                ${exercise.instructions.map(instruction => `
                                    <li>${instruction}</li>
                                `).join('')}
                            </ol>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    };

    const renderSyllabus = (response) => {
        if (response.raw_json) {
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
                            <h3>Week ${week.week}: ${week.mainTopic}</h3>
                            <div class="week-content">
                                ${marked.parse(week.description)}
                                <div class="topics-list">
                                    ${week.topics.map(topic => `
                                        <div class="topic-item">
                                            <h4>${topic.subtitle}</h4>
                                            <ul>
                                                ${topic.points.map(point => `
                                                    <li>${point}</li>
                                                `).join('')}
                                            </ul>
                                        </div>
                                    `).join('')}
                                </div>
                                ${response.weeklyContent && response.weeklyContent[week.week] ? 
                                    renderWeeklyContent(response.weeklyContent[week.week]) : 
                                    '<button class="load-content-btn" data-week="' + week.week + '">Load Detailed Content</button>'
                                }
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

    const openWeekContent = (weekNumber, topic, content) => {
        const contentHtml = renderWeeklyContent(content);
        const params = new URLSearchParams({
            content: contentHtml,
            topic: topic
        });
        window.open(`/week-content/${weekNumber}?${params}`, `week${weekNumber}`,
            'width=1200,height=800,menubar=no,toolbar=no,location=no,status=no');
    };

    const generateAllWeeklyContent = async (weeks, syllabusData) => {
        const generateAllBtn = document.getElementById('generateAllContent');
        let completedCount = 0;
        
        generateAllBtn.disabled = true;
        generateAllBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating Content (0/' + weeks.length + ')';
    
        try {
            for (const week of weeks) {
                const weekContainer = document.querySelector(`div.week-block:nth-child(${week.week}) .week-content`);
                const loadingDiv = document.createElement('div');
                loadingDiv.className = 'loading';
                loadingDiv.innerHTML = 'Generating content...';
                weekContainer.appendChild(loadingDiv);
    
                try {
                    const contentResponse = await fetch('/generate/week-content', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ weekData: week })
                    });
                    
                    const data = await contentResponse.json();
                    if (data.error) throw new Error(data.error);
                    
                    // Replace loading div with view button
                    const viewButton = document.createElement('button');
                    viewButton.className = 'view-content-btn';
                    viewButton.innerHTML = '<i class="fas fa-eye"></i> View Week Content';
                    viewButton.onclick = () => openWeekContent(week.week, week.mainTopic, data.content);
                    
                    loadingDiv.replaceWith(viewButton);
                    completedCount++;
                    generateAllBtn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Generating Content (${completedCount}/${weeks.length})`;
                    
                } catch (error) {
                    loadingDiv.innerHTML = '<div class="error-message"><i class="fas fa-exclamation-circle"></i> Failed to generate content</div>';
                    console.error(`Error generating content for week ${week.week}:`, error);
                }
            }
        } finally {
            generateAllBtn.disabled = false;
            generateAllBtn.innerHTML = '<i class="fas fa-check"></i> Content Generation Complete';
            setTimeout(() => {
                generateAllBtn.innerHTML = '<i class="fas fa-list-check"></i> Regenerate All Weekly Content';
            }, 3000);
        }
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

            // Show bulk actions after successful syllabus generation
            const bulkActionsDiv = document.getElementById('bulk-actions');
            bulkActionsDiv.style.display = 'block';
            
            // Add event listener for bulk generation
            document.getElementById('generateAllContent').addEventListener('click', () => {
                generateAllWeeklyContent(data.response.raw_json.weeklyTopics, data.response.raw_json);
            });
            
            // Store syllabus data globally
            window.syllabusData = data.response.raw_json;
            
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

    // Add event listener for loading content
    document.addEventListener('click', async (e) => {
        if (e.target.classList.contains('load-content-btn')) {
            const btn = e.target;
            const weekNum = btn.dataset.week;
            const weekData = window.syllabusData.weeklyTopics.find(w => w.week == weekNum);
            
            try {
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
                
                const contentResponse = await fetch('/generate/week-content', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ weekData })
                });
                
                const data = await contentResponse.json();
                if (data.error) throw new Error(data.error);
                
                // Replace button with view button
                const viewButton = document.createElement('button');
                viewButton.className = 'view-content-btn';
                viewButton.innerHTML = '<i class="fas fa-eye"></i> View Week Content';
                viewButton.onclick = () => openWeekContent(weekNum, weekData.mainTopic, data.content);
                
                btn.replaceWith(viewButton);
            } catch (error) {
                console.error('Error:', error);
                btn.innerHTML = '<i class="fas fa-exclamation-circle"></i> Error generating content';
            }
        }
    });
});