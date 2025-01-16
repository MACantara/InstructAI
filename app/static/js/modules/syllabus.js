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
    if (!activities || !activities.length) return '';
    
    return `
        <div class="mt-4">
            <div class="card border-primary border-opacity-25">
                <div class="card-header bg-primary bg-opacity-10">
                    <h4 class="h5 mb-0">In-Class Activities</h4>
                </div>
                <div class="list-group list-group-flush">
                    ${activities.map(activity => `
                        <div class="list-group-item">
                            <div class="d-flex justify-content-between align-items-start">
                                <div>
                                    <h5 class="h6 mb-1">${activity.title}</h5>
                                    <p class="mb-0 text-secondary">${activity.description}</p>
                                </div>
                                <span class="badge bg-primary rounded-pill">${activity.duration}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
};

const renderWeeklyAssignments = (assignments) => {
    if (!assignments || !assignments.length) return '';
    
    return `
        <div class="mt-4">
            <div class="card border-success border-opacity-25">
                <div class="card-header bg-success bg-opacity-10">
                    <h4 class="h5 mb-0">Assignments</h4>
                </div>
                <div class="list-group list-group-flush">
                    ${assignments.map(assignment => `
                        <div class="list-group-item">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <h5 class="h6 mb-0">${assignment.title}</h5>
                                <div class="badges">
                                    <span class="badge bg-warning text-dark me-1">Due: ${assignment.dueDate}</span>
                                    <span class="badge bg-info">Weight: ${assignment.weightage}</span>
                                </div>
                            </div>
                            <p class="mb-0 text-secondary">${assignment.description}</p>
                        </div>
                    `).join('')}
                </div>
            </div>
        </div>
    `;
};

export const renderWeeklyQuiz = (quiz) => {
    if (!quiz) return '';
    
    return `
        <div class="mt-4">
            <div class="card border-info border-opacity-25">
                <div class="card-header bg-info bg-opacity-10 d-flex justify-content-between align-items-center">
                    <h4 class="h5 mb-0">${quiz.title}</h4>
                    <span class="badge bg-info">${quiz.duration}</span>
                </div>
                <div class="card-body">
                    <div class="row g-3">
                        <div class="col-md-4">
                            <div class="d-flex align-items-center">
                                <i class="fas fa-clipboard-list text-info me-2"></i>
                                <div>
                                    <small class="text-muted d-block">Format</small>
                                    <strong>${quiz.format}</strong>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="d-flex align-items-center">
                                <i class="fas fa-question-circle text-info me-2"></i>
                                <div>
                                    <small class="text-muted d-block">Questions</small>
                                    <strong>${quiz.numQuestions}</strong>
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4">
                            <div class="d-flex align-items-center">
                                <i class="fas fa-star text-info me-2"></i>
                                <div>
                                    <small class="text-muted d-block">Total Points</small>
                                    <strong>${quiz.totalPoints}</strong>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
};
