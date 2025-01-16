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
        <div class="container-fluid p-0">
            <div class="mb-4">
                <h1 class="display-5 text-primary">${json.title || 'Untitled Syllabus'}</h1>
                
                <div class="row g-4">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-body prose">
                                <h2 class="card-title h4">Course Description</h2>
                                ${typeof json.courseDescription === 'string' ? 
                                    marked.parse(json.courseDescription) : 
                                    'No description available'}
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-12">
                        <div class="card">
                            <div class="card-body">
                                <h2 class="card-title h4">Course Structure</h2>
                                <ul class="list-unstyled">
                                    <li class="mb-2"><span class="fw-bold">Duration:</span> ${json.courseStructure.duration}</li>
                                    <li class="mb-2"><span class="fw-bold">Format:</span> ${json.courseStructure.format}</li>
                                    <li class="mb-2"><span class="fw-bold">Assessment:</span> ${json.courseStructure.assessment}</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div class="weekly-topics mt-5">
                <h2 class="h3 mb-4">Weekly Topics</h2>
                ${validWeeks.map(week => `
                    <div class="card mb-4">
                        <div class="card-header bg-light">
                            <h3 class="h5 mb-0">Week ${week.week}: ${week.mainTopic}</h3>
                        </div>
                        <div class="card-body">
                            ${marked.parse(week.description)}
                            <div class="row g-3 mt-3">
                                ${week.topics.map(topic => `
                                    <div class="col-md-4">
                                        <div class="card h-100">
                                            <div class="card-body">
                                                <h4 class="h6 card-title">${topic.subtitle}</h4>
                                                <ul class="list-group list-group-flush">
                                                    ${topic.points.map(point => `
                                                        <li class="list-group-item">${point}</li>
                                                    `).join('')}
                                                </ul>
                                            </div>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                            
                            ${renderWeeklyActivities(week.activities)}
                            ${renderWeeklyAssignments(week.assignments)}
                            ${renderWeeklyQuiz(week.quiz)}
                            
                            <button class="btn btn-primary mt-3 load-content-btn" data-week="${week.week}">
                                Load Detailed Content
                            </button>
                        </div>
                    </div>
                `).join('')}
            </div>
            ${renderOptionalSections(json)}
        </div>
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
        <div class="mt-4">
            <h4 class="h5 mb-3">In-Class Activities</h4>
            <div class="list-group">
                ${activities.map(activity => `
                    <div class="list-group-item">
                        <div class="d-flex justify-content-between align-items-center">
                            <strong>${activity.title}</strong>
                            <span class="badge bg-secondary">${activity.duration}</span>
                        </div>
                        <p class="mb-0 mt-2">${activity.description}</p>
                    </div>
                `).join('')}
            </div>
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
