import { configureMarkdown } from './renderer.js';

export const renderSyllabus = (response) => {
    if (!response.raw_json) {
        return typeof response.text === 'string' ? 
            marked.parse(response.text) : 
            'Invalid response format';
    }
    
    const json = response.raw_json;

    // Validate topic structure
    const validateWeek = (week) => {
        if (!Array.isArray(week.topics) || week.topics.length !== 3) {
            console.error(`Week ${week.week}: Invalid number of topics`);
            return false;
        }
        return week.topics.every(topic => 
            Array.isArray(topic.points) && topic.points.length >= 3);
    };

    // Filter out invalid weeks
    const validWeeks = json.weeklyTopics.filter(validateWeek);

    if (validWeeks.length !== json.weeklyTopics.length) {
        console.error('Some weeks have invalid topic structure');
    }

    return `
        <div class="syllabus-header">
            <h1>${json.title || 'Untitled Syllabus'}</h1>
        </div>
        
        <div class="course-info">
            <div class="course-description">
                <h2>Course Description</h2>
                ${typeof json.courseDescription === 'string' ? 
                    marked.parse(json.courseDescription) : 
                    'No description available'}
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
            ${validWeeks.map(week => `
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
                        
                        ${renderWeeklyActivities(week.activities)}
                        ${renderWeeklyAssignments(week.assignments)}
                        ${renderWeeklyQuiz(week.quiz)}
                        
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

export const renderWeeklyActivities = (activities) => {
    if (!activities || activities.length === 0) return '';
    
    return `
        <div class="activities-section">
            <h4>In-Class Activities</h4>
            ${activities.map(activity => `
                <div class="activity-item">
                    <strong>${activity.title}</strong> (${activity.duration})
                    <p>${activity.description}</p>
                </div>
            `).join('')}
        </div>
    `;
};

const renderWeeklyAssignments = (assignments) => {
    if (!assignments || assignments.length === 0) return '';
    
    return `
        <div class="assignments-section">
            <h4>Assignments</h4>
            ${assignments.map(assignment => `
                <div class="assignment-item">
                    <strong>${assignment.title}</strong>
                    <div class="assignment-meta">Due: ${assignment.dueDate} | Weight: ${assignment.weightage}</div>
                    <p>${assignment.description}</p>
                </div>
            `).join('')}
        </div>
    `;
};

export const renderWeeklyQuiz = (quiz) => {
    if (!quiz) return '';
    
    return `
        <div class="quiz-section">
            <h4>Quiz</h4>
            <div class="quiz-header">
                <strong>${quiz.title}</strong>
            </div>
            <div class="quiz-meta">
                <ul>
                    <li><strong>Duration:</strong> ${quiz.duration}</li>
                    <li><strong>Format:</strong> ${quiz.format}</li>
                    <li><strong>Questions:</strong> ${quiz.numQuestions}</li>
                    <li><strong>Total Points:</strong> ${quiz.totalPoints}</li>
                </ul>
            </div>
        </div>
    `;
};
