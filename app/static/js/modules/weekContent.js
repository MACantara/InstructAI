import { renderWeeklyActivities, renderWeeklyQuiz } from './syllabus.js';

const ensureArray = (arr) => Array.isArray(arr) ? arr : [];

export const renderWeeklyContent = (weekContent) => {
    if (!weekContent) return '<div class="error-message">No content available</div>';
    
    if (!weekContent.content || !weekContent.content.lecture) {
        console.error('Invalid content structure:', weekContent);
        return '<div class="error-message">Invalid content structure</div>';
    }
    
    const lecture = weekContent.content.lecture;
    const resources = weekContent.content.resources || {};
    const exercises = ensureArray(weekContent.content.exercises);
    
    return `
        <div class="week-content-details">
            <div class="lecture-content markdown-body">
                ${marked.parse(lecture.notes)}
            </div>

            <div class="slides-section">
                ${marked.parse(lecture.slides.join('\n'))}
            </div>

            <div class="examples-section">
                ${marked.parse(lecture.examples.join('\n\n'))}
            </div>

            ${weekContent.content.activities ? renderWeeklyActivities(weekContent.content.activities) : ''}
            ${renderResources(resources)}
            ${weekContent.content.quiz ? renderWeeklyQuiz(weekContent.content.quiz) : ''}
            ${renderExercises(exercises)}
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

const renderExercises = (exercises) => {
    if (!exercises || exercises.length === 0) return '';
    
    return `
        <div class="exercises-section">
            <h4>Exercises</h4>
            ${exercises.map(exercise => `
                <div class="exercise-item difficulty-${exercise.difficulty || 'unknown'}">
                    <h5>${exercise.title || 'Untitled Exercise'}</h5>
                    <p>${exercise.description || ''}</p>
                    <ol>
                        ${ensureArray(exercise.instructions).map(instruction => `
                            <li>${instruction}</li>
                        `).join('')}
                    </ol>
                </div>
            `).join('')}
        </div>
    `;
};

export const openWeekContent = (weekNumber, topic, content) => {
    try {
        const contentHtml = renderWeeklyContent(content);
        const params = new URLSearchParams({
            content: contentHtml,
            topic: topic || 'Weekly Content'
        });
        window.open(`/week-content/${weekNumber}?${params}`, `week${weekNumber}`,
            'width=1200,height=800,menubar=no,toolbar=no,location=no,status=no');
    } catch (error) {
        console.error('Error opening week content:', error);
        alert('Failed to open week content. Please try again.');
    }
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
