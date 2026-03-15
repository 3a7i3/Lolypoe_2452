class LearningDirector:
    def learn(self, performance):
        insights = {}
        if performance["profit"] > 0:
            insights["reinforce"] = True
        else:
            insights["adjust"] = True
        return insights
