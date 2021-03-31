$(document).ready(function() {

  $('button.g-recaptcha').click(function(e) {
    console.log('Verifying recaptcha');
    var $this = $(this);
    e.preventDefault();
    grecaptcha.ready(function() {
      grecaptcha.execute($this.data('sitekey'), {action: 'submit'}).then(function(token) {
        $this.parents('form').prepend('<input type="hidden" name="token" value="' + token + '">');
        $this.parents('form').submit();
      });
    });
  });

});
