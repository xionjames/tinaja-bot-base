plugins {
    kotlin("jvm") version "2.2.20"
    application
}

repositories {
    mavenCentral()
    maven("https://jitpack.io") // builds the tinaja SDK straight from the tinaja-bot-base repo
}

dependencies {
    $jvm_sdk_dependency
    testImplementation(kotlin("test"))
    testImplementation(platform("org.junit:junit-bom:5.13.4"))
    testRuntimeOnly("org.junit.platform:junit-platform-launcher")
}
$jvm_sdk_sources
kotlin {
    compilerOptions { jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_21 }
}

java {
    sourceCompatibility = JavaVersion.VERSION_21
    targetCompatibility = JavaVersion.VERSION_21
}

application {
    mainClass = "bot.BotKt"
}

tasks.test {
    useJUnitPlatform()
}
