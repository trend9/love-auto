// note.com埋め込みを全記事に自動追加
document.addEventListener('DOMContentLoaded', function () {
    // note埋め込みHTMLを作成
    const noteEmbedContainer = document.createElement('div');
    noteEmbedContainer.className = 'note-embed-container';
    noteEmbedContainer.style.cssText = 'margin: 40px 0; text-align: center;';

    noteEmbedContainer.innerHTML = `
        <iframe class="note-embed" src="https://note.com/embed/notes/n1ed1987b6cc4" 
                style="border: 0; display: block; max-width: 99%; width: 494px; padding: 0px; margin: 10px auto; position: static; visibility: visible;" 
                height="400"></iframe>
    `;

    // 挿入位置を特定(.back-areaの前)
    const backArea = document.querySelector('.back-area');
    if (backArea && backArea.parentNode) {
        backArea.parentNode.insertBefore(noteEmbedContainer, backArea);

        // note.comの埋め込みスクリプトを動的に読み込み
        const script = document.createElement('script');
        script.src = 'https://note.com/scripts/embed.js';
        script.async = true;
        script.charset = 'utf-8';
        document.body.appendChild(script);
    }
});
