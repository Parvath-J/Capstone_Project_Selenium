pipeline {
    // Specify a Windows agent by label (make sure this label exists)
    agent { label 'windows' }

    // NO tools block needed
    // NO environment block needed

    stages {
        stage('Checkout Code') {
            steps {
                cleanWs()
                git(
                    url: 'https://github.com/Parvath-J/Capstone_Project_Selenium.git',
                    branch: 'main'
                )
            }
        }

        stage('Setup Python Environment') {
            steps {
                bat '''
                echo --- Navigating into Project Directory ---
                cd Capstone_Selenium_Pytest

                echo --- Setting up Python Virtual Environment ---
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

        stage('Run Pytest Selenium Tests') {
            steps {
                bat '''
                echo --- Activating Environment & Running Tests ---
                cd Capstone_Selenium_Pytest
                CALL ".\\venv\\Scripts\\activate.bat"

                echo --- Running Pytest with Edge ---
                pytest -v --browser edge --alluredir=allure-results
                SET PYTEST_EXIT_CODE=%ERRORLEVEL%

                echo --- Deactivating Environment (Tests Complete) ---
                CALL ".\\venv\\Scripts\\deactivate.bat"

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

            archiveArtifacts artifacts: 'Capstone_Selenium_Pytest/allure-results/**/*', allowEmptyArchive: true
            cleanWs()
        }
        success {
            echo 'Build succeeded!'
        }
        failure {
            echo 'Build failed.'
        }
        unstable {
            echo 'Build unstable (tests likely failed).'
        }
    }
}