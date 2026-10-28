#!/usr/bin/env bash
# Runs every demo one after another. Usage: bash run-all.sh
set -e
cd "$(dirname "$0")"

mvn -q compile

for main in \
  com.example.spring.di.DependencyInjectionDemo \
  com.example.spring.scope.BeanScopeLifecycleDemo \
  com.example.spring.config.ConfigurationProfilesDemo \
  com.example.spring.aop.AopDemo \
  com.example.spring.tx.TransactionDemo \
  com.example.spring.events.EventsDemo
do
  echo
  echo "=================== ${main##*.} ==================="
  mvn -q exec:java -Dexec.mainClass="$main"
done
