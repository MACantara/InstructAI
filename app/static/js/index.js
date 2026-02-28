import { openWeekContent, generateAllWeeklyContent } from './modules/weekContent.js';

document.addEventListener('DOMContentLoaded', () => {
    const elements = {
        form: document.getElementById('syllabusForm'),
        generateBtn: document.getElementById('generate'),
        topicInput: document.getElementById('topic'),
        responseArea: document.getElementById('response'),
        bulkActions: document.getElementById('bulk-actions')
    };

    const updateWeekContentUI = (weekNum, weeklyTopicId, courseId, completedCount, totalCount, error = null) => {
        const weekContainer = document.querySelector(`.week-content[data-week="${weekNum}"]`);
        const generateAllBtn = document.getElementById('generateAllContent');

        if (error) {
            weekContainer.innerHTML = `
                <div class="alert alert-danger d-flex align-items-center gap-2">
                    <i class="fas fa-exclamation-circle"></i> Failed to generate content
                </div>`;
        } else {
            const viewButton = document.createElement('button');
            viewButton.className = 'btn btn-primary d-inline-flex align-items-center gap-2';
            viewButton.innerHTML = '<i class="fas fa-eye"></i> View Week Content';
            viewButton.onclick = () => openWeekContent(weekNum, weeklyTopicId, courseId);
            weekContainer.innerHTML = '';
            weekContainer.appendChild(viewButton);
        }

        if (generateAllBtn) {
            const buttonText = completedCount === totalCount ? 
                '<i class="fas fa-check me-2"></i> Content Generation Complete' :
                `<i class="fas fa-spinner fa-spin me-2"></i> Generating Content (${completedCount}/${totalCount})`;
            
            generateAllBtn.innerHTML = buttonText;
            generateAllBtn.className = `btn w-100 d-flex align-items-center justify-content-center ${
                completedCount === totalCount ? 
                'btn-success' : 
                'btn-primary'
            }`;
            generateAllBtn.disabled = completedCount !== totalCount;
        }
    };

    elements.form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const topic = elements.topicInput.value.trim();
        if (!topic) return;

        try {
            elements.generateBtn.disabled = true;
            elements.generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Generating Syllabus...';
            elements.generateBtn.classList.add('disabled');
            
            elements.responseArea.innerHTML = `
                <div class="d-flex align-items-center justify-content-center p-4">
                    <div class="text-primary">
                        <i class="fas fa-spinner fa-spin fa-2x me-3"></i>
                        Creating your syllabus...
                    </div>
                </div>`;

            const response = await fetch('/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    topic: topic
                })
            });

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Render a simple week list
            const weeks = data.response.raw_json.weeklyTopics;
            elements.responseArea.innerHTML = `
                <div class="card shadow-sm">
                    <div class="card-header bg-white">
                        <h2 class="h5 mb-0"><i class="fas fa-list me-2 text-primary"></i>${data.response.raw_json.title}</h2>
                    </div>
                    <div class="list-group list-group-flush">
                        ${weeks.map(week => `
                            <div class="list-group-item d-flex justify-content-between align-items-center">
                                <div>
                                    <span class="fw-bold">Week ${week.week}:</span> ${week.mainTopic}
                                </div>
                                <div class="week-content" data-week="${week.week}">
                                    <button class="btn btn-sm btn-outline-primary load-content-btn" data-week="${week.week}">
                                        <i class="fas fa-cog me-1"></i> Generate Content
                                    </button>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                </div>`;

            // Show bulk actions after successful syllabus generation
            elements.bulkActions.classList.remove('d-none');
            
            if (data.response.course_id) {
                // Store course_id globally for use in weekly content generation
                window.courseId = data.response.course_id;
            }

            // Update bulk generation event listener to include courseId
            document.getElementById('generateAllContent').addEventListener('click', () => {
                if (!window.courseId) {
                    console.error('No course ID available');
                    return;
                }
                generateAllWeeklyContent(
                    data.response.raw_json.weeklyTopics, 
                    window.courseId,  // Pass the stored courseId
                    updateWeekContentUI
                );
            });
            
            // Store syllabus data globally
            window.syllabusData = data.response.raw_json;
            
        } catch (error) {
            console.error('Error:', error);
            elements.responseArea.innerHTML = `
                <div class="alert alert-danger d-flex align-items-center gap-3">
                    <i class="fas fa-exclamation-circle"></i>
                    <span>Error generating syllabus: ${error.message}</span>
                </div>`;
        } finally {
            elements.generateBtn.disabled = false;
            elements.generateBtn.innerHTML = 'Generate Syllabus';
            elements.generateBtn.classList.remove('disabled');
        }
    });

    document.addEventListener('click', async (e) => {
        if (e.target.classList.contains('load-content-btn')) {
            const btn = e.target;
            const weekNum = btn.dataset.week;
            const weekData = window.syllabusData.weeklyTopics.find(w => w.week == weekNum);
            
            if (!window.courseId) {
                console.error('No course ID available');
                return;
            }

            try {
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Generating...';
                btn.classList.add('disabled');
                
                const contentResponse = await fetch('/generate/week-content', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        weekData,
                        courseId: window.courseId  // Include courseId in request
                    })
                });
                
                const data = await contentResponse.json();
                if (data.error) throw new Error(data.error);
                
                // Replace button with view button using IDs
                const viewButton = document.createElement('button');
                viewButton.className = 'btn btn-primary d-inline-flex align-items-center gap-2';
                viewButton.innerHTML = '<i class="fas fa-eye"></i> View Week Content';
                viewButton.onclick = () => openWeekContent(weekNum, data.weekly_topic_id, window.courseId);
                
                btn.replaceWith(viewButton);
            } catch (error) {
                console.error('Error:', error);
                btn.innerHTML = '<i class="fas fa-exclamation-circle me-2"></i> Error generating content';
                btn.classList.replace('btn-primary', 'btn-danger');
            }
        }
    });

    // Initialize bulk actions
    if (elements.bulkActions) {
        const generateAllBtn = document.getElementById('generateAllContent');
        generateAllBtn?.addEventListener('click', () => {
            generateAllWeeklyContent(window.syllabusData.weeklyTopics, updateWeekContentUI);
        });
    }
});