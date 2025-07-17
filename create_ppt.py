import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from google.oauth2.credentials import Credentials
def create_presentation(title):
  """
  Creates the Presentation the user has access to.
  Load pre-authorized user credentials from the environment.
  TODO(developer) - See https://developers.google.com/identity
  for guides on implementing OAuth2 for the application.
  """
  SCOPES = [
      "https://www.googleapis.com/auth/presentations",
   
  ]
#   creds, _ = google.auth.default()
  creds = Credentials.from_authorized_user_file("credentials.json", SCOPES)
  # pylint: disable=maybe-no-member
  try:
    service = build("slides", "v1", credentials=creds)

    body = {"title": title,}
    presentation = service.presentations().create(body=body,supportsAllDrives=True,).execute()
    print(
        f"Created presentation with ID:{(presentation.get('presentationId'))}"
    )
    return presentation

  except HttpError as error:
    print(f"An error occurred: {error}")
    print("presentation not created")
    return error


if __name__ == "__main__":
  # Put the title of the presentation

  create_presentation("finalp")