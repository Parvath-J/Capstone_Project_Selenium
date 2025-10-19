pipeline {
    // Specify a Windows agent by label
    agent { label 'windows' }

    stages {
        stage('Checkout') {
            steps {
                // Clean the workspace before checkout
                cleanWs()
                // Checkout code from your Git repository
                git branch: 'main', url: 'https://github.com/Parvath-J/Capstone_Project_Selenium.git'
            }
        }

        stage('Setup Environment') {
            steps {
                // Use PowerShell for Windows commands
                powershell '''
                Write-Host "--- Setting up Python Virtual Environment ---"

                # Navigate into the project folder
                cd Capstone_Selenium_Pytest

                # Create venv if it doesn't exist
                if (-not (Test-Path -Path ".\venv" -PathType Container)) {
                    python -m venv venv
                    if ($LASTEXITCODE -ne 0) {
                        Write-Error "Failed to create virtual environment"
                        exit 1
                    }
                } else {
                    Write-Host "Virtual environment already exists."
                }

                Write-Host "--- Installing Dependencies ---"
                # Activate venv and install requirements
                .\venv\Scripts\Activate.ps1
                pip install -r requirements.txt
                if ($LASTEXITCODE -ne 0) {
                    Write-Error "Failed to install dependencies"
                    # Deactivate before exiting
                    try { Deactivate-Venv } catch {}
                    exit 1
                }

                Write-Host "--- Deactivating Environment (Setup Complete) ---"
                # Deactivate venv after install for clean state in next stage
                try { Deactivate-Venv } catch {}
                '''
            }
        }

        stage('Run Tests') {
            steps {
                // Use PowerShell again
                powershell '''
                Write-Host "--- Activating Environment & Running Tests ---"

                # Navigate into the project folder
                cd Capstone_Selenium_Pytest

                # Activate venv
                .\venv\Scripts\Activate.ps1

                Write-Host "--- Running Pytest with Edge ---"
                # Run pytest, generate Allure results
                pytest -v --browser edge --alluredir=allure-results
                if ($LASTEXITCODE -ne 0) {
                    Write-Warning "Pytest execution failed!"
                    # Don't exit immediately, let Allure report generation run
                }

                Write-Host "--- Deactivating Environment (Tests Complete) ---"
                try { Deactivate-Venv } catch {}
                '''
            }
        }
    }

    post {
        // This 'always' block runs regardless of build success or failure
        always {
            // Generate and archive the Allure report
            allure includeProperties: false,
                   jdk: '', // Use default JDK configured in Jenkins
                   reportBuildPolicy: 'ALWAYS', // Generate report even for failures
                   results: [[path: 'Capstone_Selenium_Pytest/allure-results']] // Path to results relative to workspace root
        }
        success {
            echo 'Build succeeded!'
        }
        failure {
            echo 'Build failed.'
        }
    }
}