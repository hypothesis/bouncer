#!groovy

@Library('pipeline-library') _

def img

node {
    stage('build') {
        checkout(scm)
        img = buildApp(name: 'hypothesis/bouncer')
    }

    stage('checkformatting') {
        testApp(image: img, runArgs: '-u root') {
            installDeps()
            run('tox -e checkformatting')
        }
    }

    stage('lint') {
        testApp(image: img, runArgs: '-u root') {
            installDeps()
            run('tox -e lint')
        }
    }

    stage('test') {
        testApp(image: img, runArgs: '-u root') {
            installDeps()
            run('tox')
            run('tox -e coverage')
        }
    }

    onlyOnMaster {
        stage('release') {
            releaseApp(image: img)
        }
    }
}

onlyOnMaster {
    milestone()
    stage('qa deploy') {
        deployApp(image: img, app: 'bouncer', env: 'qa')
    }

    milestone()
    stage('prod deploy') {
        input(message: "Deploy to prod?")
        milestone()
        deployApp(image: img, app: 'bouncer', env: 'prod')
    }
}


/**
 * Install some common system dependencies.
 *
 * These are test dependencies that're need to run most of the stages above
 * (tests, lint, ...) but that aren't installed in the production Docker image.
 */
def installDeps() {
    sh 'pip install -q tox>=3.8.0'
}

/** Run the given command. */
def run(command) {
    sh "apk add build-base"
    sh "cd /var/lib/bouncer && ${command}"
}
