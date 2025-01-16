import { renderMetadata, configureMarkdown } from './modules/renderer.js';
import { renderSyllabus } from './modules/syllabus.js';
import { openWeekContent, generateAllWeeklyContent } from './modules/weekContent.js';

document.addEventListener('DOMContentLoaded', () => {
    const elements = {
        form: document.getElementById('syllabusForm'),
        generateBtn: document.getElementById('generate'),
        topicInput: document.getElementById('topic'),
        responseArea: document.getElementById('response'),
        includeObjectives: document.getElementById('includeObjectives'),
        includeReadings: document.getElementById('includeReadings'),
        bulkActions: document.getElementById('bulk-actions')
    };

    configureMarkdown();

    const updateWeekContentUI = (weekNum, topic, content, completedCount, totalCount, error = null) => {
        const weekContainer = document.querySelector(`div.week-block:nth-child(${weekNum}) .week-content`);
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
            viewButton.onclick = () => openWeekContent(weekNum, topic, content);
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
                        <i class="fas fa-graduation-cap fa-2x me-3"></i>
                        Creating your syllabus...
                    </div>
                </div>`;

            const response = await fetch('/generate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    topic: topic,
                    include_objectives: elements.includeObjectives.checked,
                    include_readings: elements.includeReadings.checked
                })
            });

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            // Update response area with structured syllabus and sources
            elements.responseArea.innerHTML = `
                <div class="card shadow-sm">
                    <div class="card-body">
                        <div class="syllabus-content prose">
                            ${renderSyllabus(data.response)}
                        </div>
                        ${renderMetadata(data.response.metadata)}
                    </div>
                </div>`;

            // Show bulk actions after successful syllabus generation
            elements.bulkActions.classList.remove('d-none');
            
            // Add event listener for bulk generation
            document.getElementById('generateAllContent').addEventListener('click', () => {
                generateAllWeeklyContent(data.response.raw_json.weeklyTopics, updateWeekContentUI);
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
            
            try {
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i> Generating...';
                btn.classList.add('disabled');
                
                const contentResponse = await fetch('/generate/week-content', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ weekData })
                });
                
                const data = await contentResponse.json();
                if (data.error) throw new Error(data.error);
                
                // Replace button with view button
                const viewButton = document.createElement('button');
                viewButton.className = 'btn btn-primary d-inline-flex align-items-center gap-2';
                viewButton.innerHTML = '<i class="fas fa-eye"></i> View Week Content';
                viewButton.onclick = () => openWeekContent(weekNum, weekData.mainTopic, data.content);
                
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