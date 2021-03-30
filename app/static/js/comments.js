$(document).ready(function() {

  $('form').each(function() {
    var $this = $(this);
    if ($this.find('input#captcha').length) {
      var submitBtn = $this.find('button[type="submit"]');
      var captcha = $this.find('input#captcha');
      if (captcha.prop('checked') == false) {
        submitBtn.addClass('disabled').prop('disabled',true);
      }
    }
  });

  $('input#captcha').click(function() {
    if ($(this).prop('checked') == true) {
      $(this).parent('div').parent('form').find('button[type="submit"]').removeClass('disabled').prop('disabled',false);
    }
  });

  $('input#name').parent('div.form-group').slideUp().hide();
  $('input#email').parent('div.form-group').slideUp().hide();
  $('input#subscribe').parent('div.form-group').slideUp().hide();
  $('input#captcha').parent('div.form-group').slideUp().hide();

  $('textarea#body').focus(function() {
    $('input#name').parent('div.form-group').slideDown().show();
    $('input#email').parent('div.form-group').slideDown().show();
    $('input#subscribe').parent('div.form-group').slideDown().show();
    $('input#captcha').parent('div.form-group').slideDown().show();
  });

});
