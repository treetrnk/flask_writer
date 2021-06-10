$(document).ready(function() {

  $('input#name').parent('div.form-group').slideUp().hide();
  $('input#email').parent('div.form-group').slideUp().hide();
  $('input#subscribe').parent('div.form-group').slideUp().hide();
  $('.captcha').slideUp().hide();

  $('textarea#body').focus(function() {
    $('input#name').parent('div.form-group').slideDown().show();
    $('input#email').parent('div.form-group').slideDown().show();
    $('input#subscribe').parent('div.form-group').slideDown().show();
    $('.captcha').slideDown().show();
  });

  var commentForm = $('#comment-form');
  var replyInd = $('#reply-indicator');

  $('.comment-reply-btn').click(function() {
    var $this = $(this);
    console.log(commentForm);
    console.log(replyInd);
    commentForm.find('input#reply_id').val($this.data('id'));
    replyInd.fadeIn().show();
    replyInd.find('#reply-username').text($this.data('username'));
    replyInd.find('#reply-date').text($this.data('date'));
    commentForm.find('textarea#body').focus();
  });

  $('#reply-remove').click(function() {
    replyInd.hide();
    commentForm.find('input#reply_id').val('');
  });

});
