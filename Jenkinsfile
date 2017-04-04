#!groovy

node {
    stage 'Build'
    checkout scm

    // Store the short commit id for use tagging images
    sh 'git rev-parse --short HEAD > GIT_SHA'
    gitSha = readFile('GIT_SHA').trim()

    sh "make docker DOCKER_TAG=${gitSha}"
    img = docker.image "hypothesis/bouncer:${gitSha}"

    stage 'Test'
    // Run our Python tests inside the built container
    img.inside("-u root") {
        sh 'pip install -q tox'
        sh 'cd /var/lib/bouncer && tox'
    }

    // We only push the image to the Docker Hub if we're on master
    if (env.BRANCH_NAME != 'master') {
        return
    }
    stage 'Push'
    docker.withRegistry('', 'docker-hub-build') {
        img.push('auto')
    }
}
