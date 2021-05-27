$(document).ready(function(){ 
  $('.cancel').hide();
  $('.confirm').hide();
  $('.delete').click(function(){
    $(this).siblings('.cancel').show();
    $(this).siblings('.confirm').show();
    $(this).hide();
  });
  $('.cancel').click(function(){
    $(this).siblings('.confirm').hide();
    $(this).siblings('.delete').show();
    $(this).hide();
  });
  var form = document.querySelector('#adminform'); 
  form.onsubmit = function() { 
    var about = document.querySelector('input[name=adminMessage]'); 
    about.value = JSON.stringify(quill.root.innerHTML);
  };
  var form2 = document.querySelector('#userform'); 
  form2.onsubmit = function() { 
    var about2 = document.querySelector('input[name=userMessage]'); 
    about2.value = JSON.stringify(quill2.root.innerHTML);
  }; 
  const limit = 5000;
  quill.on('text-change', function (delta, old, source) {
    if (quill.getLength() > limit) {
      quill.deleteText(limit, quill.getLength());
    }
  });
});
