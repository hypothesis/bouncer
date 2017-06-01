#!groovy

node {
    stage 'Build'
    checkout scm

    buildVersion = sh(
        script: 'python3 -c "import bouncer; print(bouncer.__version__)"',
        returnStdout: true
    ).trim()

    // Docker tags may not contain '+'
    dockerTag = buildVersion.replace('+', '-')

    // Set build metadata
    currentBuild.displayName = buildVersion
    currentBuild.description = "Docker: ${dockerTag}"

    // Build docker image
    sh "make docker DOCKER_TAG=${dockerTag}"
    img = docker.image "hypothesis/bouncer:${dockerTag}"

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
        img.push()
        img.push('latest')
    }
}
