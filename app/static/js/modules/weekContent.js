export const renderWeeklyContent = (weekContent) => {
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
                                    <p>${video.description}</p>
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
                                    <p>${article.relevance}</p>
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
                                    <p>${tool.purpose}</p>
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

export const openWeekContent = (weekNumber, topic, content) => {
    const contentHtml = renderWeeklyContent(content);
    const params = new URLSearchParams({
        content: contentHtml,
        topic: topic
    });
    window.open(`/week-content/${weekNumber}?${params}`, `week${weekNumber}`,
        'width=1200,height=800,menubar=no,toolbar=no,location=no,status=no');
};

export const generateAllWeeklyContent = async (weeks, updateUI) => {
    let completedCount = 0;
    
    for (const week of weeks) {
        try {
            const contentResponse = await fetch('/generate/week-content', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ weekData: week })
            });
            
            const data = await contentResponse.json();
            if (data.error) throw new Error(data.error);
            
            updateUI(week.week, week.mainTopic, data.content, ++completedCount, weeks.length);
            
        } catch (error) {
            console.error(`Error generating content for week ${week.week}:`, error);
            updateUI(week.week, null, null, completedCount, weeks.length, error);
        }
    }
};
