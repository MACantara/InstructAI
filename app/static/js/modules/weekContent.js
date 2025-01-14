export const renderWeeklyContent = (weekContent) => {
    if (!weekContent) return '';
    
    // Sort videos and articles by source (AI-generated vs metadata)
    const sortResources = (resources, type) => {
        return resources[type].sort((a, b) => {
            const aFromMeta = a.url?.includes('vertexaisearch.cloud.google.com') || false;
            const bFromMeta = b.url?.includes('vertexaisearch.cloud.google.com') || false;
            return aFromMeta === bFromMeta ? 0 : aFromMeta ? -1 : 1;
        });
    };
    
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

            ${renderWeeklyActivities(weekContent.content.activities)}

            <div class="resources-section">
                <h4>Additional Resources</h4>
                ${renderResources(weekContent.content.resources)}
            </div>

            ${weekContent.content.quiz ? `
                <div class="quiz-info-section">
                    <h4>Quiz Information</h4>
                    <div class="quiz-meta">
                        <ul>
                            <li><strong>Duration:</strong> ${weekContent.content.quiz.duration}</li>
                            <li><strong>Format:</strong> ${weekContent.content.quiz.format}</li>
                            <li><strong>Questions:</strong> ${weekContent.content.quiz.numQuestions}</li>
                            <li><strong>Total Points:</strong> ${weekContent.content.quiz.totalPoints}</li>
                        </ul>
                    </div>
                </div>
            ` : ''}

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

const renderResources = (resources) => {
    return `
        ${resources.videos.length > 0 ? renderResourceSection('📺 Videos', resources.videos, 'video') : ''}
        ${resources.articles.length > 0 ? renderResourceSection('📚 Articles', resources.articles, 'article') : ''}
        ${resources.tools.length > 0 ? renderResourceSection('🛠️ Tools', resources.tools, 'tool') : ''}
    `;
};

const renderResourceSection = (title, items, type) => {
    return `
        <div class="${type}s">
            <h5>${title}</h5>
            <ul>
                ${items.map(item => `
                    <li class="${item.url?.includes('vertexaisearch') ? 'meta-source' : ''}">
                        <a href="${item.url}" target="_blank" rel="noopener">
                            ${item.title || item.name}
                        </a>
                        <p>${item.description || item.purpose || item.relevance}</p>
                    </li>
                `).join('')}
            </ul>
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
