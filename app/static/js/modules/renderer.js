/**
 * Configures the global marked.js instance with common options.
 * Call this once before any markdown parsing.
 */
export const configureMarkdown = () => {
    if (typeof marked === 'undefined') return;
    marked.setOptions({
        breaks: true,
        gfm: true,
    });
};
