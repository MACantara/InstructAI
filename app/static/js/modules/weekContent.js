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

const renderWeeklyHeader = (weekNum, topic, description) => `
    <div class="card mb-4">
        <div class="card-body">
            <h1 class="display-6">Week ${weekNum}: ${topic}</h1>
            <p class="lead text-secondary">${description}</p>
        </div>
    </div>
`;

const renderLecture = (lecture) => {
    if (!lecture?.notes) return '';
    
    const parsedNotes = marked.parse(lecture.notes);
    
    return `
        <div class="card mb-4">
            <div class="card-header bg-primary bg-opacity-10">
                <h2 class="h5 mb-0">Lecture Content</h2>
            </div>
            <div class="card-body prose">
                ${parsedNotes}
            </div>
            ${lecture.slides?.length ? `
                <div class="card-footer bg-light">
                    <h3 class="h6 mb-3">Lecture Slides</h3>
                    <div class="list-group list-group-flush">
                        ${lecture.slides.map(slide => `
                            <div class="list-group-item">
                                <i class="fas fa-file-powerpoint text-primary me-2"></i>
                                ${slide}
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
        </div>
    `;
};

const renderTopicsOverview = (topics) => {
    if (!topics?.length) return '';
    
    return `
        <div class="card mb-4">
            <div class="card-header bg-info bg-opacity-10">
                <h2 class="h5 mb-0">Topics Overview</h2>
            </div>
            <div class="card-body">
                <div class="row g-4">
                    ${topics.map((topic, index) => `
                        <div class="col-md-4">
                            <div class="card h-100 border-info border-opacity-25">
                                <div class="card-header bg-info bg-opacity-10">
                                    <h3 class="h6 mb-0">${topic.subtitle}</h3>
                                </div>
                                <div class="card-body">
                                    <ul class="list-unstyled mb-0">
                                        ${topic.points.map(point => `
                                            <li class="mb-2">
                                                <i class="fas fa-check text-info me-2"></i>
                                                ${point}
                                            </li>
                                        `).join('')}
                                    </ul>
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
};

export const renderWeeklyContent = (weekContent) => {
    if (!weekContent) return '<div class="alert alert-danger">No content available</div>';
    
    return `
        <div class="container-fluid py-4">
            ${renderWeeklyHeader(
                weekContent.week_number,
                weekContent.main_topic,
                weekContent.description
            )}
            
            ${renderTopicsOverview(weekContent.topics)}
            
            <div class="row g-4">
                <div class="col-lg-8">
                    ${renderLecture(weekContent.content.lecture)}
                    ${renderExercises(weekContent.content.exercises)}
                </div>
                <div class="col-lg-4">
                    ${renderResources(weekContent.content.resources)}
                    ${renderWeeklyActivities(weekContent.content.activities)}
                    ${renderWeeklyQuiz(weekContent.content.quiz)}
                </div>
            </div>
        </div>
    `;
};

const renderResources = (resources) => {
    return `
        <div class="col-12">
            <div class="card">
                <div class="card-header bg-light">
                    <h4 class="mb-0">Learning Resources</h4>
                </div>
                <div class="card-body">
                    <div class="row g-4">
                        ${resources.videos.length > 0 ? `
                            <div class="col-md-4">
                                <div class="card h-100 border-primary border-opacity-25">
                                    <div class="card-header bg-primary bg-opacity-10">
                                        <h5 class="h6 mb-0">
                                            <i class="fas fa-video me-2"></i>Video Resources
                                        </h5>
                                    </div>
                                    ${renderResourceList(resources.videos, 'video')}
                                </div>
                            </div>
                        ` : ''}
                        ${resources.articles.length > 0 ? `
                            <div class="col-md-4">
                                <div class="card h-100 border-info border-opacity-25">
                                    <div class="card-header bg-info bg-opacity-10">
                                        <h5 class="h6 mb-0">
                                            <i class="fas fa-book me-2"></i>Reading Materials
                                        </h5>
                                    </div>
                                    ${renderResourceList(resources.articles, 'article')}
                                </div>
                            </div>
                        ` : ''}
                        ${resources.tools.length > 0 ? `
                            <div class="col-md-4">
                                <div class="card h-100 border-success border-opacity-25">
                                    <div class="card-header bg-success bg-opacity-10">
                                        <h5 class="h6 mb-0">
                                            <i class="fas fa-tools me-2"></i>Tools & Software
                                        </h5>
                                    </div>
                                    ${renderResourceList(resources.tools, 'tool')}
                                </div>
                            </div>
                        ` : ''}
                    </div>
                </div>
            </div>
        </div>
    `;
};

const renderResourceList = (items, type) => {
    return `
        <div class="list-group list-group-flush">
            ${items.map(item => `
                <div class="list-group-item">
                    <a href="${item.url}" class="text-decoration-none" target="_blank" rel="noopener">
                        <h6 class="mb-1">${item.title || item.name}</h6>
                    </a>
                    <p class="mb-0 small text-secondary">
                        ${item.description || item.purpose || item.relevance}
                    </p>
                </div>
            `).join('')}
        </div>
    `;
};

const renderExercises = (exercises) => {
    if (!exercises || !exercises.length) return '';
    
    const difficultyClasses = {
        beginner: 'border-success',
        intermediate: 'border-warning',
        advanced: 'border-danger',
        unknown: 'border-secondary'
    };
    
    const difficultyBadges = {
        beginner: 'bg-success',
        intermediate: 'bg-warning text-dark',
        advanced: 'bg-danger',
        unknown: 'bg-secondary'
    };

    return `
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h4 class="mb-0">Practice Exercises</h4>
                </div>
                <div class="card-body">
                    <div class="row g-4">
                        ${exercises.map(exercise => `
                            <div class="col-md-6">
                                <div class="card h-100 ${difficultyClasses[exercise.difficulty || 'unknown']} border-opacity-50">
                                    <div class="card-header d-flex justify-content-between align-items-center">
                                        <h5 class="h6 mb-0">${exercise.title || 'Untitled Exercise'}</h5>
                                        <span class="badge ${difficultyBadges[exercise.difficulty || 'unknown']}">
                                            ${exercise.difficulty || 'Unknown'} Level
                                        </span>
                                    </div>
                                    <div class="card-body">
                                        <p class="card-text text-secondary mb-3">${exercise.description || ''}</p>
                                        <ol class="list-group list-group-numbered">
                                            ${ensureArray(exercise.instructions).map(instruction => `
                                                <li class="list-group-item">${instruction}</li>
                                            `).join('')}
                                        </ol>
                                    </div>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        </div>
    `;
};

export const openWeekContent = async (weekNum, weeklyTopicId, courseId) => {
    if (!weeklyTopicId) {
        console.error('Weekly topic ID is missing');
        return;
    }

    try {
        // First verify content exists
        const response = await fetch(`/api/week-content/${weeklyTopicId}`);
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Open content in new window/tab
        const url = `/week-content/${weekNum}?id=${weeklyTopicId}&course_id=${courseId}`;
        window.open(url, '_blank');
        
    } catch (error) {
        console.error('Failed to open week content:', error);
        alert('Failed to open week content: ' + error.message);
    }
};

export const generateAllWeeklyContent = async (weeks, courseId, updateUI) => {
    if (!weeks?.length || !courseId) {
        console.error('Missing required data for bulk generation');
        return;
    }

    const totalWeeks = weeks.length;
    let completedCount = 0;

    for (const weekData of weeks) {
        try {
            const response = await fetch('/generate/week-content', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ weekData, courseId })
            });
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            completedCount++;
            updateUI?.(
                weekData.week, 
                data.weekly_topic_id, 
                courseId, 
                completedCount, 
                totalWeeks
            );
            
        } catch (error) {
            console.error(`Error generating content for week ${weekData.week}:`, error);
            updateUI?.(
                weekData.week, 
                null, 
                courseId, 
                completedCount, 
                totalWeeks, 
                error
            );
        }
    }
};
