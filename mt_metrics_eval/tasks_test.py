# coding=utf-8
# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Tests for stats."""

import io
from mt_metrics_eval import tasks
import numpy as np
import unittest


class TaskTest(unittest.TestCase):

  def testPostInitPearsonCorr(self):
    task = tasks.Task()
    ref_task = tasks.Task(gold='mqm', refs={'refA'}, close_refs=set())
    self.assertEqual(task, ref_task)

    task = tasks.Task(test_set='wmt21.news')
    ref_task = tasks.Task(
        test_set='wmt21.news', lang='en-de',
        gold='mqm', refs={'refC'}, close_refs=set())
    self.assertEqual(task, ref_task)

  def testPostInitAccuracyCorr(self):
    task = tasks.Task(
        test_set='wmt21.news', lang='en-de,en-ru,zh-en', corr_fcn='accuracy')
    ref_task = tasks.Task(
        test_set='wmt21.news', lang='en-de,en-ru,zh-en', corr_fcn='accuracy',
        gold=['mqm', 'mqm', 'mqm'],
        refs=[{'refC'}, {'refA'}, {'refB'}],
        close_refs=[set(), set(), set()])
    self.assertEqual(task, ref_task)

    task = tasks.Task(
        test_set='wmt21.news', lang='en-de', corr_fcn='accuracy')
    ref_task = tasks.Task(
        test_set='wmt21.news', lang='en-de', corr_fcn='accuracy',
        gold=['mqm'], refs=[{'refC'}], close_refs=[set()])
    self.assertEqual(task, ref_task)

  def testRunDefault(self):
    ref_metrics = [
        'metricx_xxl_MQM_2020', 'COMET-20', 'COMET-22', 'BLEURT-20', 'MATESE',
        'UniTE', 'MS-COMET-22', 'COMETKiwi[noref]', 'SEScore',
        'UniTE-src[noref]', 'YiSi-1', 'COMET-QE[noref]',
        'MS-COMET-QE-22[noref]', 'MEE4', 'MATESE-QE[noref]', 'BERTScore',
        'HWTSC-Teacher-Sim[noref]', 'HuaweiTSC_EE_BERTScore_0.3_With_Human',
        'f200spBLEU', 'chrF', 'BLEU', 'REUSE[noref]']
    results = tasks.Task(k=1).Run()
    self.assertEqual(results.metrics, ref_metrics)
    self.assertAlmostEqual(results.Corr('metricx_xxl_MQM_2020'), 0.8619197)
    self.assertEqual(results.Rank('metricx_xxl_MQM_2020'), 1)
    self.assertAlmostEqual(results.Corr('REUSE[noref]'), -0.5138621)

  def testRunAccuracy(self):
    ref_metrics = [
        'metricx_xxl_MQM_2020', 'COMET-20', 'COMET-22', 'BLEURT-20', 'UniTE',
        'MATESE', 'COMET-QE[noref]', 'MS-COMET-22', 'YiSi-1', 'MEE4',
        'BERTScore', 'UniTE-src[noref]', 'COMETKiwi[noref]', 'SEScore',
        'MS-COMET-QE-22[noref]', 'BLEU', 'chrF', 'f200spBLEU',
        'HuaweiTSC_EE_BERTScore_0.3_With_Human', 'MATESE-QE[noref]',
        'HWTSC-Teacher-Sim[noref]', 'REUSE[noref]']
    results = tasks.Task(corr_fcn='accuracy', k=1).Run()
    self.assertEqual(results.metrics, ref_metrics)
    self.assertAlmostEqual(results.Corr('metricx_xxl_MQM_2020'), 0.8021978)
    self.assertEqual(results.Rank('metricx_xxl_MQM_2020'), 1)
    self.assertAlmostEqual(results.Corr('REUSE[noref]'), 0.3296703)


class TaskResultsTest(unittest.TestCase):

  def testAttrVals(self):
    task = tasks.Task()
    res = tasks.TaskResults(task, (None, None))
    attr_vals = res.attr_vals
    for attr in tasks.Attributes():
      self.assertEqual(attr_vals[attr], f'{task.StrVal(attr)}')

  def testResultsString(self):
    results = ({'m1': (0.111111111, 1), 'metric2': (0.222222222, 2)},
               np.array([[0, 0.01], [0, 0]]))
    res = tasks.TaskResults(tasks.Task(), results)
    self.assertEqual(
        res.Str(), 'm1       1  0.1111111  . >\nmetric2  2  0.2222222  . . \n')

  def testWriteRead(self):
    fh = io.StringIO()
    res_out = tasks.Task(k=1).Run()
    res_out.Write(fh)
    fh.seek(0)
    res_in = tasks.TaskResults().Read(fh)
    self.assertEqual(res_out, res_in)


class TaskSetTest(unittest.TestCase):

  def testConstruction(self):
    attr_combs = {
        'lang': ['en-de', 'en-ru', 'zh-en'],
        'domain': [None, 'conversation', 'ecommerce', 'news', 'social'],
        'level': ['sys', 'seg']
    }
    taskset = tasks.TaskSet(attr_combs, k=10)
    # pylint: disable=g-generic-assert
    self.assertEqual(len(taskset), 3 * 5 * 2)

    en_de_count = sum(t.lang == 'en-de' for t in taskset)
    self.assertEqual(en_de_count, 10)

    k10_count = sum(t.k == 10 for t in taskset)
    self.assertEqual(k10_count, 30)

    taskset = tasks.TaskSet()
    self.assertEqual(len(taskset), 0)  # pylint: disable=g-generic-assert

  def testAdd(self):
    tasks1 = tasks.TaskSet({'lang': ['en-de']})
    tasks2 = tasks.TaskSet({'lang': ['en-ru']})
    tasks3 = tasks.TaskSet({'lang': ['zh-en']})
    sum_tasks = tasks1 + tasks2 + tasks3
    all_tasks = tasks.TaskSet({'lang': ['en-de', 'en-ru', 'zh-en']})
    self.assertEqual(sum_tasks.tasks, all_tasks.tasks)

  def testRun(self):
    taskset = tasks.TaskSet({'corr_fcn': ['pearson', 'accuracy']}, k=1)
    res = taskset.Run()
    self.assertEqual(len(res), 2)  # pylint: disable=g-generic-assert

    ref_pearson = tasks.Task(corr_fcn='pearson', k=1).Run()
    self.assertEqual(res.results[0].metrics, ref_pearson.metrics)

    ref_acc = tasks.Task(corr_fcn='accuracy', k=1).Run()
    self.assertEqual(res.results[1].metrics, ref_acc.metrics)


class TaskSetResultsTest(unittest.TestCase):

  def Results(self):
    taskset = tasks.TaskSet(
        {'lang': ['en-de,en-ru,zh-en']}, corr_fcn='accuracy', k=1)
    taskset += tasks.TaskSet(
        {'lang': ['en-de', 'en-ru', 'zh-en'], 'corr_fcn': ['pearson']}, k=1)
    taskset += tasks.TaskSet(
        {'lang': ['en-de', 'en-ru'], 'corr_fcn': ['kendall']}, k=1)
    return taskset.Run()

  def testSplitByAttr(self):
    results = self.Results()
    splits = results.SplitByAttr('lang')
    self.assertEqual(len(splits), 4)  # pylint: disable=g-generic-assert
    self.assertEqual(
        list(splits.keys()), ['en-de,en-ru,zh-en', 'en-de', 'en-ru', 'zh-en'])
    # pylint: disable=g-generic-assert
    self.assertEqual(len(splits['en-de,en-ru,zh-en']), 1)
    self.assertEqual(len(splits['en-de']), 2)
    self.assertEqual(len(splits['en-ru']), 2)
    self.assertEqual(len(splits['zh-en']), 1)

  def testAssignWeights(self):
    results = self.Results()

    weights = results.AssignWeights(tasks.Attributes())
    self.assertEqual(weights, [1/4, 1/8, 1/8, 1/4, 1/8, 1/8])

    weights = results.AssignWeights(['corr_fcn'])
    self.assertEqual(weights, [1/3, 1/9, 1/9, 1/9, 1/6, 1/6])

    weights = results.AssignWeights(['test_set'])
    self.assertEqual(weights, [1/6] * 6)

    weights = results.AssignWeights([])
    self.assertEqual(weights, [1/6] * 6)

  def testAverageRanks(self):
    results = self.Results()
    ranks = results.AverageRanks()
    self.assertEqual(len(ranks), 21)  # pylint: disable=g-generic-assert
    self.assertEqual(list(ranks.values()), sorted(ranks.values()))
    self.assertTrue(all(r >= 1 for r in ranks.values()))


if __name__ == '__main__':
  unittest.main()
