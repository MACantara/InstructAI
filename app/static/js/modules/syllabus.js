import { configureMarkdown } from './renderer.js';

export const renderSyllabus = (response) => {
    if (!response.raw_json) return marked.parse(response.text);
    
    const json = response.raw_json;
    return `
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
                                        ${topic.points.map(point => `<li>${point}</li>`).join('')}
                                    </ul>
                                </div>
                            `).join('')}
                        </div>
                        <button class="load-content-btn" data-week="${week.week}">Load Detailed Content</button>
                    </div>
                </div>
            `).join('')}
        </div>
        ${renderOptionalSections(json)}
    `;
};

const renderOptionalSections = (json) => {
    let html = '';
    
    if (json.learningObjectives) {
        html += `
            <div class="objectives">
                <h2>Learning Objectives</h2>
                <ul>
                    ${json.learningObjectives.map(obj => `<li>${obj}</li>`).join('')}
                </ul>
            </div>`;
    }
    
    if (json.readings) {
        html += `
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
            </div>`;
    }
    
    return html;
};
