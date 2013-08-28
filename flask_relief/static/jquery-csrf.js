var csrf_token = $('meta[name=csrf-token]').attr('content');

$.ajaxSetup({
  beforeSend: function(xhr, settings) {
    if (!/^(GET|HEAD)$/i.test(settings.type)) {
      xhr.setRequestHeader('X-RELIEF-CSRF-TOKEN', csrf_token);
    }
  }
});
