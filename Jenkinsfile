pipeline {
    agent any

    stages {
        stage('Checkout Code') {
            steps {
                cleanWs()
                git branch: 'main', url: 'https://github.com/Parvath-J/Capstone_Project_Selenium.git'
            }
        }

        stage('Setup Python Environment') {
            steps {
                dir('Capstone_Selenium_Pytest') {
                    bat '''
                    echo --- Setting up Python Virtual Environment ---
                    C:\\Users\\Ascendion\\AppData\\Local\\Programs\\Python\\Python313\\python.exe -m venv venv
                    call venv\\Scripts\\activate.bat
                    python -m pip install --upgrade pip
                    pip install -r requirements.txt
                    '''
                }
            }
        }

        stage('Run Selenium Pytest Tests') {
            steps {
                dir('Capstone_Selenium_Pytest') {
                    bat '''
                    echo --- Running Tests ---
                    call venv\\Scripts\\activate.bat
                    pytest --browser edge --alluredir=allure-results
                    '''
                }
            }
        }
    }

    post {
        always {
            echo '--- Generating Allure Report ---'
            allure includeProperties: false,
                   jdk: '',
                   commandline: 'Allure',
                   results: [[path: 'Capstone_Selenium_Pytest/allure-results']]
        }

        success {
            echo '✅ Build succeeded!'
        }

        failure {
            echo '❌ Build failed.'
        }
    }
}