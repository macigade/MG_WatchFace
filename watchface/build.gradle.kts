plugins {
    id("com.android.application")
}

android {
    namespace = "com.macigade.mgwatchface"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.macigade.mgwatchface"

        // Watch Face Format 2 requires Wear OS 5 (API 34). The Galaxy Watch 7
        // shipped with Wear OS 5, so 34 is the correct floor for this project.
        minSdk = 34
        targetSdk = 34

        versionCode = 1
        versionName = "1.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }
}
