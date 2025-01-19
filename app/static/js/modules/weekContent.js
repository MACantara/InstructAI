import { configureMarkdown } from './renderer.js';

// Only keep the core functionality needed for content generation and opening
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
