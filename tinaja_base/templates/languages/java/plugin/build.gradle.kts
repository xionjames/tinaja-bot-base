plugins {
    application
}

repositories {
    mavenCentral()
    maven("https://jitpack.io") // builds the tinaja SDK straight from the tinaja-bot-base repo
}

dependencies {
    $jvm_sdk_dependency
    testImplementation(platform("org.junit:junit-bom:5.13.4"))
    testImplementation("org.junit.jupiter:junit-jupiter")
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}
$jvm_sdk_sources
tasks.withType<JavaCompile> { options.release = 21 }

application {
    mainClass = "bot.Bot"
}

tasks.test {
    useJUnitPlatform()
}
