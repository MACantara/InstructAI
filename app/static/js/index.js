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
            weekContainer.innerHTML = `<div class="error-message">
                <i class="fas fa-exclamation-circle"></i> Failed to generate content
            </div>`;
        } else {
            const viewButton = document.createElement('button');
            viewButton.className = 'view-content-btn';
            viewButton.innerHTML = '<i class="fas fa-eye"></i> View Week Content';
            viewButton.onclick = () => openWeekContent(weekNum, topic, content);
            weekContainer.innerHTML = '';
            weekContainer.appendChild(viewButton);
        }

        if (generateAllBtn) {
            generateAllBtn.innerHTML = completedCount === totalCount ? 
                '<i class="fas fa-check"></i> Content Generation Complete' :
                `<i class="fas fa-spinner fa-spin"></i> Generating Content (${completedCount}/${totalCount})`;
        }
    };

    // Event Handlers
    elements.form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const topic = elements.topicInput.value.trim();
        if (!topic) return;

        try {
            elements.generateBtn.disabled = true;
            elements.generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating Syllabus...';
            elements.responseArea.innerHTML = '<div class="loading">🎓 Creating your syllabus...</div>';

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
                <div class="syllabus-content markdown-body">
                    ${renderSyllabus(data.response)}
                </div>
                ${renderMetadata(data.response.metadata)}
            `;

            // Show bulk actions after successful syllabus generation
            elements.bulkActions.style.display = 'block';
            
            // Add event listener for bulk generation
            document.getElementById('generateAllContent').addEventListener('click', () => {
                generateAllWeeklyContent(data.response.raw_json.weeklyTopics, updateWeekContentUI);
            });
            
            // Store syllabus data globally
            window.syllabusData = data.response.raw_json;
            
        } catch (error) {
            console.error('Error:', error);
            elements.responseArea.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-circle"></i>
                    Error generating syllabus: ${error.message}
                </div>
            `;
        } finally {
            elements.generateBtn.disabled = false;
            elements.generateBtn.innerHTML = 'Generate Syllabus';
        }
    });

    document.addEventListener('click', async (e) => {
        if (e.target.classList.contains('load-content-btn')) {
            const btn = e.target;
            const weekNum = btn.dataset.week;
            const weekData = window.syllabusData.weeklyTopics.find(w => w.week == weekNum);
            
            try {
                btn.disabled = true;
                btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
                
                const contentResponse = await fetch('/generate/week-content', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ weekData })
                });
                
                const data = await contentResponse.json();
                if (data.error) throw new Error(data.error);
                
                // Replace button with view button
                const viewButton = document.createElement('button');
                viewButton.className = 'view-content-btn';
                viewButton.innerHTML = '<i class="fas fa-eye"></i> View Week Content';
                viewButton.onclick = () => openWeekContent(weekNum, weekData.mainTopic, data.content);
                
                btn.replaceWith(viewButton);
            } catch (error) {
                console.error('Error:', error);
                btn.innerHTML = '<i class="fas fa-exclamation-circle"></i> Error generating content';
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