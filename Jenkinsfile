pipeline {
    agent { label 'windows' } // Ensure this label matches your Windows agent

    stages {
        stage('Checkout') {
            steps {
                cleanWs()
                git branch: 'main', url: 'https://github.com/Parvath-J/Capstone_Project_Selenium.git'
            }
        }

        stage('Setup Environment') {
            steps {
                // Use Windows Batch step
                bat '''
                echo --- Setting up Python Virtual Environment ---

                REM Navigate into the project folder
                cd Capstone_Selenium_Pytest

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

        stage('Run Tests') {
            steps {
                // Use Windows Batch step again
                bat '''
                echo --- Activating Environment & Running Tests ---

                REM Navigate into the project folder
                cd Capstone_Selenium_Pytest

                REM Activate venv using the .bat script
                CALL ".\\venv\\Scripts\\activate.bat"

                echo --- Running Pytest with Edge ---
                REM Run pytest, generate Allure results
                pytest -v --browser edge --alluredir=allure-results
                SET PYTEST_EXIT_CODE=%ERRORLEVEL%

                echo --- Deactivating Environment (Tests Complete) ---
                CALL ".\\venv\\Scripts\\deactivate.bat"

                REM Exit with pytest's exit code to correctly set build status
                exit /b %PYTEST_EXIT_CODE%
                '''
            }
        }
    }

    post {
        always {
            allure includeProperties: false,
                   jdk: '',
                   reportBuildPolicy: 'ALWAYS',
                   results: [[path: 'Capstone_Selenium_Pytest/allure-results']]
        }
        success {
            echo 'Build succeeded!'
        }
        failure {
            echo 'Build failed.'
        }
    }
}