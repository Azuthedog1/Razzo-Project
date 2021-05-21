var toolbarOptions = [
  ['bold', 'italic', 'underline', 'strike'],
  ['link'],
  [{ 'header': 1 }, { 'header': 2 }],               // custom button values
  [{ 'list': 'ordered'}, { 'list': 'bullet' }],
  [{ 'indent': '-1'}, { 'indent': '+1' }],          // outdent/indent
  [{ 'direction': 'rtl' }],                         // text direction

  [{ 'size': ['small', false, 'large', 'huge'] }],  // custom dropdown
  [{ 'header': [1, 2, 3, 4, 5, 6, false] }],

  [{ 'align': [] }],

  ['clean']                                         // remove formatting button
];

var quill = new Quill('#editor-container', {
  modules: {
    toolbar: toolbarOptions
  },
  theme: 'snow'
});

var form = document.querySelector('form');
form.onsubmit = function() {
  // Populate hidden form on submit
  var about = document.querySelector('input[name=about]');
  about.value = JSON.stringify(quill.getContents());
  
  console.log("Submitted", $(form).serialize(), $(form).serializeArray());
  
  // No back end to actually submit to!
  alert('Open the console to see the submit data!')
  return false;
};
