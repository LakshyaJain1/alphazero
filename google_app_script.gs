// Set up a time-driven trigger to run the checkRecentEmails function every minute
function setUpTrigger() {
  ScriptApp.newTrigger('checkRecentEmails')
      .timeBased()
      .everyMinutes(1)
      .create();
}

function checkRecentEmails() {
  var emailAddress = 'meet-transcriptions-noreply@google.com';
  var oneMinuteAgo = new Date();
  oneMinuteAgo.setMinutes(oneMinuteAgo.getMinutes() - 1);
  var formattedDate = Utilities.formatDate(oneMinuteAgo, Session.getScriptTimeZone(), 'yyyy/MM/dd HH:mm:ss');

  Logger.log(formattedDate);

  var searchQuery = 'in:inbox from:' + emailAddress + ' newer_than:1h ';

  Logger.log(searchQuery);

  var threads = GmailApp.search(searchQuery);

  threads.forEach(function(thread) {
    var messages = thread.getMessages();

    messages.forEach(function(message) {
      if (message.isUnread()) {
      var subject = message.getSubject();
      Logger.log('Subject: ' + subject);
      checkFileContentsByName(subject);
      message.markRead
      }
    });
  });
}

function checkFileContentsByName(fileName) {
  var files = DriveApp.getFilesByName(fileName);

  if (files.hasNext()) {
    var file = files.next();
    Logger.log('File Name: ' + file.getName());

    var fileId = file.getId();
    Logger.log('File Id:\n' + fileId);

    var file = DriveApp.getFileById(fileId);

    if (file.getMimeType() === 'application/vnd.google-apps.document') {
      var doc = DocumentApp.openById(fileId);
      var docContent = doc.getBody().getText();
      Logger.log(docContent.toString());
      //sendHttpRequestToPythonService(docContent.toString());
    }
  } else {
    Logger.log('File with name "' + fileName + '" not found in Google Drive.');
  }
}

function sendHttpRequestToPythonService(docContentData) {
  var url = 'https://26a2-13-126-193-149.ngrok-free.app/generate-summary';
  var headers = {
    'ngrok-skip-browser-warning': 'anyValueHere',
    'Content-Type': 'application/json'
  };

  var requestBody = {
    key: docContentData,
  };

  var options = {
    'method': 'post',
    'headers': headers,
    'muteHttpExceptions': true,
    'payload': JSON.stringify(requestBody)
  };

  var response = UrlFetchApp.fetch(url, options);

  Logger.log(response.getContentText());
}
