from string import digits, punctuation

from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import generic
from django.views.generic.edit import FormView, UpdateView


def clean_search_phrase(phrase) -> list[str]:
    for char in punctuation + digits:
        phrase = phrase.replace(char, " ")
    words = phrase.split()
    words_list = []
    for word in words:
        if word:
            word = word.capitalize()
            words_list.append(word)
            if word[-1] == "s":
                words_list.append(word[:-1])
    return words_list


class EditorOnlyMixin:
    def get(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            if self.request.user.profile.is_editor:
                return super().get(request, *args, **kwargs)
        return redirect(reverse_lazy('newsharborapp:home'))
