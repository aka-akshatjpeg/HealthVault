# Firebase Authentication Setup

HealthVault now uses Firebase Authentication for Google, Apple, and phone OTP on the Flask website and in the Expo mobile app. Firebase verifies the user; the backend verifies the Firebase ID token and then creates a HealthVault session (web) or HealthVault JWTs (mobile). New Firebase sign-ups receive the patient role. Existing HealthVault roles are preserved when a verified Firebase email is linked.

## Firebase project and app registrations

Use project ID `healthvault-68880` and enable Google, Apple, and Phone in Firebase Console under **Authentication → Sign-in method**.

Register these apps in the same Firebase project:

- Web app: used by the Flask login page.
- Android app ID: `com.healthvault.mobile`.
- iOS bundle ID: `com.healthvault.mobile`.

Download the native app settings files and place them here:

- `HealthVaultMobile/google-services.json`
- `HealthVaultMobile/GoogleService-Info.plist`

The project already points Expo at these paths, and Git ignores both files. Do not rename or commit them.

## Website configuration

Open the Firebase web app settings and copy its web configuration into `backend/.env`:

```dotenv
FIREBASE_PROJECT_ID=healthvault-68880
FIREBASE_WEB_API_KEY=<apiKey from the web app config>
FIREBASE_WEB_AUTH_DOMAIN=healthvault-68880.firebaseapp.com
FIREBASE_WEB_APP_ID=<appId from the web app config>
```

If Firebase shows a different `authDomain`, use that exact value. Add the deployed HealthVault website host to Firebase Authentication's authorized domains. Web phone OTP uses Firebase's reCAPTCHA verifier; Firebase does not allow localhost as the hosted domain for web phone authentication, so test that flow on an authorized HTTPS host or with Firebase test phone numbers.

The backend uses Firebase Admin to verify ID tokens. For local development, configure Google Application Default Credentials for the same Firebase project, or set `GOOGLE_APPLICATION_CREDENTIALS` in the server environment to a service-account JSON file stored outside this repository. In production, use the hosting platform's service identity. Never put a service-account private key in this project, `.env.example`, the app, or chat.

## Mobile configuration

Set these values in `HealthVaultMobile/.env.local`:

```dotenv
EXPO_PUBLIC_API_URL=http://<your-computer-LAN-IP>:5000/api/v1
EXPO_PUBLIC_FIREBASE_PROJECT_ID=healthvault-68880
EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID=<Google OAuth web client ID>
EXPO_PUBLIC_FIREBASE_APPLE_SERVICE_ID=<Apple Services ID>
EXPO_PUBLIC_FIREBASE_APPLE_REDIRECT_URI=https://<domain-you-control>/<registered-return-path>
```

For Google Sign-In, use the OAuth **web client ID** from the Google Cloud credentials associated with this Firebase project. Register the Android package and its debug/release signing SHA-1 and SHA-256 fingerprints in Firebase/Google Cloud. For a physical phone, the API URL must use the computer's LAN IP, not `localhost`.

For Apple Sign-In, enable the matching app ID in Apple Developer. The website uses Firebase's Apple provider. Android also needs an Apple Services ID and an HTTPS Return URL registered on that Services ID; Apple does not accept localhost or an IP address for that URL. Configure the Apple Team ID, key ID, and private key in Firebase Console, not in the Expo app. iOS uses the app's Apple Sign-In capability and does not need the Services ID runtime variables.

Phone OTP uses native Firebase app verification in the mobile app. Configure allowed SMS regions in Firebase and use Firebase test phone numbers during development to avoid sending real SMS messages.

## Build and run

These Firebase native modules require an Expo development build; Expo Go cannot load them. After adding the native files and environment settings, generate and build the native app. On Windows, Android can be built locally with the Android SDK. iOS builds require a Mac or an EAS cloud build with the required Apple signing setup.

```powershell
cd HealthVaultMobile
npm.cmd run prebuild
npx expo run:android
npm.cmd run dev-client
```

Start the Flask backend separately and make sure the mobile `EXPO_PUBLIC_API_URL` points to its reachable LAN address. Restart Expo after changing `.env.local`, and rebuild the native app after changing native Firebase files, OAuth client configuration, or Expo plugins.

## Phone-only accounts

A phone-authenticated user may not have an email address. Since the current users table requires one, HealthVault stores a generated non-routable `@healthvault.invalid` value for those accounts and does not accept an email typed by the client as proof of ownership. That placeholder is omitted from patient API responses.

## Link an existing HealthVault account to phone sign-in

In the mobile app, choose **Already have a HealthVault account? Link it** before requesting the Firebase phone code. Enter the account's current email and password, then complete Firebase phone verification. The backend verifies the Firebase ID token and the current password, links the Firebase UID, and preserves the account's existing role. It does not match accounts using a phone number stored in an old profile. The password is sent only to the HealthVault backend over HTTPS in production; it is not sent to Firebase or stored by the mobile app. If the account is already linked to a different Firebase identity, contact the HealthVault administrator rather than attempting to merge accounts.
