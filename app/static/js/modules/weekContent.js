import { configureMarkdown } from './renderer.js';
import { renderWeeklyActivities, renderWeeklyQuiz } from './syllabus.js';

const safeMarkdownParse = (text) => {
    if (!text) return '';
    try {
        // Handle object or string input
        const processedText = typeof text === 'object' ? 
            (text.text || JSON.stringify(text)) : 
            String(text);
            
        // Clean up any markdown formatting issues
        const cleanText = processedText
            .replace(/^#+\s*/, '')  // Remove leading #'s
            .trim();
            
        return marked.parse(cleanText);
    } catch (e) {
        console.warn('Markdown parsing failed:', e);
        return String(text);
    }
};

const formatParagraphs = (text) => {
    return text
        // Split into paragraphs on double newlines
        .split(/\n\n+/)
        .filter(p => p.trim())
        .map(p => `<p class="content-paragraph">${p.trim()}</p>`)
        .join('\n');
};

const formatSectionContent = (content) => {
    // First, split content into sections based on numbered headers
    const sections = content.split(/(?=^\d+\.)/gm);
    
    return sections.map(section => {
        // Process each section
        const lines = section.split('\n');
        let formattedSection = '';
        
        // Extract section title if it exists (numbered header)
        if (lines[0].match(/^\d+\./)) {
            formattedSection += `<h2 class="section-title">${lines.shift()}</h2>\n`;
        }
        
        // Process remaining lines
        const subsections = lines.join('\n').split(/(?=^\d+\.\d+\.)/gm);
        
        return subsections.map(subsection => {
            const subLines = subsection.split('\n');
            let formattedSubsection = '';
            
            // Extract subsection title if it exists
            if (subLines[0].match(/^\d+\.\d+\./)) {
                formattedSubsection += `<h3 class="subtopic-title">${subLines.shift()}</h3>\n`;
            }
            
            // Group the remaining content
            const paragraphs = subLines.join('\n')
                .replace(/\*\*([^*]+)\*\*/g, '<span class="key-term">$1</span>')
                .replace(/\*([^*]+)\*/g, '<em class="emphasis">$1</em>')
                .replace(/^-\s+(.+)$/gm, '<li>$1</li>') // Convert bullet points
                .replace(/(?:^|\n)>\s*([^\n]+)/g, '<blockquote class="quote-block">$1</blockquote>'); // Format quotes
            
            // Wrap bullet points in ul if they exist
            const hasListItems = paragraphs.includes('<li>');
            const formattedParagraphs = hasListItems ? 
                paragraphs.replace(/(<li>.*<\/li>\n*)+/g, '<ul>$&</ul>') :
                formatParagraphs(paragraphs);
                
            formattedSubsection += formattedParagraphs;
            
            return `<div class="subtopic">${formattedSubsection}</div>`;
        }).join('\n');
        
    }).join('\n<hr class="separator">\n');
};

const formatSlides = (slides) => {
    return `
        <div class="slides-section">
            <h2 class="section-header">Key Points</h2>
            ${slides.map(slide => `
                <div class="slide-item">${slide}</div>
            `).join('')}
        </div>
    `;
};

const formatExamples = (examples) => {
    if (!examples || !examples.length) return '';
    
    return `
        <div class="examples-section">
            <h2 class="section-header">Examples</h2>
            ${examples.map(example => {
                // Split example into title and details if it contains a colon
                const [title, ...details] = example.split(':');
                return `
                    <div class="example-item">
                        <h4>${title}${details.length ? ':' : ''}</h4>
                        ${details.length ? `<p>${details.join(':').trim()}</p>` : ''}
                    </div>
                `;
            }).join('')}
        </div>
    `;
};

const ensureArray = (arr) => Array.isArray(arr) ? arr : [];

export const renderWeeklyContent = (weekContent) => {
    if (!weekContent) return '<div class="error-message">No content available</div>';
    
    // Validate content structure
    if (!weekContent.content || !weekContent.content.lecture) {
        console.error('Invalid content structure:', weekContent);
        return '<div class="error-message">Invalid content structure</div>';
    }
    
    // Ensure arrays exist
    const lecture = weekContent.content.lecture;
    const resources = weekContent.content.resources || {};
    const exercises = ensureArray(weekContent.content.exercises);
    
    return `
        <div class="week-content-details">
            <div class="lecture-content">
                <h2 class="section-header">Lecture Materials</h2>
                ${formatSectionContent(lecture.notes)}
                ${formatSlides(lecture.slides)}
                ${formatExamples(lecture.examples)}
            </div>

            ${weekContent.content.activities ? renderWeeklyActivities(weekContent.content.activities) : ''}
            ${renderResources(weekContent.content.resources || {})}
            ${weekContent.content.quiz ? renderWeeklyQuiz(weekContent.content.quiz) : ''}
            ${renderExercises(weekContent.content.exercises || [])}
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
