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
  var form = document.querySelector('#adminform'); /*creates and sends the quill message in admin form*/
  form.onsubmit = function() { 
    var about = document.querySelector('input[name=adminMessage]'); 
    about.value = JSON.stringify(quill.root.innerHTML);
  };
  var form2 = document.querySelector('#userform');  /*creates and sends the quill message in user form*/
  form2.onsubmit = function() { 
    var about2 = document.querySelector('input[name=userMessage]'); 
    about2.value = JSON.stringify(quill2.root.innerHTML);
  }; 
  const limit = 12000;  /*character limit for user posts and comments*/
  quill2.on('text-change', function (delta, old, source) {
    if (quill2.getLength() > limit) {
      quill2.deleteText(limit, quill2.getLength());
    }
  });
  var form3 = document.querySelector('#editform');  /*creates and sends the quill message in the edit post form (admin-only)*/
  form3.onsubmit = function() { 
    var about3 = document.querySelector('input[name=newMessage]'); 
    about3.value = JSON.stringify(quill3.root.innerHTML);
  }; 
});
