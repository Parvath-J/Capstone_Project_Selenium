pipeline {
    // Specify a Windows agent by label (make sure this label exists in your Jenkins setup)
    agent { label 'windows' }

    // No Node.js tools needed
    tools {}

    environment {
        // You can keep this or remove it, not strictly needed for Pytest/Selenium
        // CI = 'true'
    }

    stages {
        stage('Checkout Code') {
            steps {
                // Clean workspace before checkout
                cleanWs()
                // Checkout your Selenium project repository
                git(
                    url: 'https://github.com/Parvath-J/Capstone_Project_Selenium.git',
                    branch: 'main'
                )
            }
        }

        stage('Setup Python Environment') {
            steps {
                // Use Windows Batch commands
                bat '''
                echo --- Navigating into Project Directory ---
                cd Capstone_Selenium_Pytest

                echo --- Setting up Python Virtual Environment ---
                REM Create venv if it doesn't exist
                IF NOT EXIST ".\\venv" (
                    echo Creating virtual environment...
                    python -m venv venv
                    IF %ERRORLEVEL% NEQ 0 (
                        echo Failed to create virtual environment
                        exit /b 1
                    )
                ) ELSE (
                    echo Virtual environment already exists.
                )

                echo --- Installing Dependencies ---
                REM Activate venv using the .bat script and install requirements
                CALL ".\\venv\\Scripts\\activate.bat"
                pip install -r requirements.txt
                IF %ERRORLEVEL% NEQ 0 (
                    echo Failed to install dependencies
                    CALL ".\\venv\\Scripts\\deactivate.bat"
                    exit /b 1
                )

                echo --- Deactivating Environment (Setup Complete) ---
                CALL ".\\venv\\Scripts\\deactivate.bat"
                '''
            }
        }

        // Removed 'Install Playwright Browser' stage

        stage('Run Pytest Selenium Tests') {
            steps {
                // Use Windows Batch commands again
                bat '''
                echo --- Activating Environment & Running Tests ---

                REM Navigate into the project folder
                cd Capstone_Selenium_Pytest

                REM Activate venv using the .bat script
                CALL ".\\venv\\Scripts\\activate.bat"

                echo --- Running Pytest with Edge ---
                REM Run pytest, specifying Edge browser and generating Allure results
                pytest -v --browser edge --alluredir=allure-results
                SET PYTEST_EXIT_CODE=%ERRORLEVEL%  REM Capture exit code

                echo --- Deactivating Environment (Tests Complete) ---
                CALL ".\\venv\\Scripts\\deactivate.bat"

                REM Exit with pytest's exit code to set build status correctly
                exit /b %PYTEST_EXIT_CODE%
                '''
            }
        }

        // Removed 'Allure Report' stage with manual generation and publishHTML
        // The Allure Jenkins plugin handles this in the post section
    }

    post {
        always {
            // Use the Allure Jenkins Plugin to generate and display the report
            allure includeProperties: false,
                   jdk: '', // Use default JDK configured in Jenkins
                   reportBuildPolicy: 'ALWAYS', // Generate report even for failed builds
                   results: [[path: 'Capstone_Selenium_Pytest/allure-results']] // Path relative to workspace root

            // Archive the raw Allure results for download (optional but good practice)
            archiveArtifacts artifacts: 'Capstone_Selenium_Pytest/allure-results/**/*', allowEmptyArchive: true

            // Clean workspace after job
            cleanWs()
        }
        success {
            echo 'Build succeeded!'
        }
        failure {
            echo 'Build failed.'
        }
        // If tests fail but the build itself doesn't error out, pytest exit code > 0
        // The 'unstable' status might be set by the pytest exit code handling
        unstable {
            echo 'Build unstable (tests likely failed).'
        }
    }
}