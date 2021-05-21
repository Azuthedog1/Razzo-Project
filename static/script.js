var justHtmlContent = document.getElementById('justHtml');

editor.on('text-change', function() {
  var justHtml = editor.root.innerHTML;
  justHtmlContent.innerHTML = justHtml;
});
