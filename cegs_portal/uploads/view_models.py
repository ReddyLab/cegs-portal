def add_experiment_to_user(experiment_accession, user):
    user.experiments.append(experiment_accession)
    user.save()
